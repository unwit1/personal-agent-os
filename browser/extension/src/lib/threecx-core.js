/*
 * Agent OS: 3CX web client protocol (read side).
 *
 * The 3CX V20 web client talks to its PBX by POSTing protobuf
 * "GenericMessage"s to /MyPhone/MPWebService.asmx, authorised by a
 * MyPhoneSession header. This module encodes the few requests Agent OS needs
 * (my info + voicemail box, call history, voicemail audio) and decodes the
 * answers into plain records. Field numbers come from the web client's own
 * generated protobuf code. Shared by the content script and the Node tests,
 * so it stays free of DOM and WebExtension APIs.
 */
(function (root, factory) {
    "use strict";
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.AgentOs3cx = factory();
    }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    var ENDPOINT = "/MyPhone/MPWebService.asmx";

    // field number -> [name, type, repeated]
    var SCHEMA = {
        GenericMessage: {
            1: ["MessageId", "int32"],
            102: ["GetMyInfo", "RequestMyInfo"],
            105: ["GetFile", "RequestGetFile"],
            106: ["GetCallHistory", "RequestCallHistory"],
            201: ["MyInfo", "MyExtensionInfo"],
            203: ["FileResult", "ResponseFile"],
            204: ["CallHistory", "ResponseCallHistory"],
            268: ["ResponseVoiceMails", "VoiceMails"],
            565: ["GetVoiceMails", "RequestGetVoiceMails"]
        },
        RequestMyInfo: { 1: ["DontSendVM", "bool"] },
        RequestGetFile: { 1: ["Folder", "int32"], 2: ["FileName", "string"], 3: ["Extension", "string"], 4: ["ItemId", "int32"] },
        ResponseFile: { 1: ["Content", "bytes"] },
        RequestCallHistory: {
            1: ["CallType", "int32"], 2: ["DnOwner", "string"], 3: ["RecordLimit", "int32"], 4: ["RecordOffset", "int32"],
            5: ["Search", "string"], 6: ["From", "DateTime"], 7: ["To", "DateTime"]
        },
        RequestGetVoiceMails: {
            3: ["Offset", "int32"], 4: ["Limit", "int32"], 5: ["QueryString", "string"], 6: ["NewOld", "bool"], 7: ["StartFromId", "int32"]
        },
        MyExtensionInfo: {
            2: ["Id", "int32"], 3: ["Number", "string"], 4: ["MobileNumber", "string"], 5: ["Email", "string"],
            7: ["FirstName", "string"], 8: ["LastName", "string"], 11: ["VoiceMailBox", "VoiceMails"]
        },
        VoiceMails: { 1: ["Action", "int32"], 2: ["Items", "VoiceMail", true] },
        VoiceMail: {
            1: ["Action", "int32"], 2: ["Id", "int32"], 3: ["Folder", "int32"], 4: ["Filename", "string"],
            5: ["CallerId", "string"], 6: ["CallerName", "string"], 7: ["ReceivedAt", "DateTime"], 8: ["Duration", "int32"],
            9: ["IsNew", "bool"], 10: ["Transcription", "string"], 11: ["CallerContact", "Contact"],
            12: ["IsArchived", "bool"], 13: ["GroupBox", "string"], 14: ["HeardBy", "string"]
        },
        ResponseCallHistory: { 1: ["Records", "CallHistoryRecord", true] },
        CallHistoryRecord: { 1: ["DnOwner", "string"], 2: ["Id", "int32"], 3: ["connections", "CallHistoryConnections"] },
        CallHistoryConnections: { 1: ["parties", "CallHistoryParty", true] },
        CallHistoryParty: {
            1: ["Id", "int32"], 2: ["StartTime", "DateTime"], 3: ["ConnectedAt", "DateTime"], 4: ["EndedAt", "DateTime"],
            5: ["PartyDN", "string"], 6: ["PartyDNType", "int32"], 7: ["PartyDNName", "string"], 8: ["PartyCallerId", "string"],
            9: ["ViaRole", "int32"], 10: ["ViaDN", "string"], 11: ["ViaDNType", "int32"], 12: ["ViaDNName", "string"],
            13: ["ViaCallerId", "string"], 14: ["CallType", "int32"], 15: ["PartyContact", "Contact"], 16: ["ViaContact", "Contact"]
        },
        Contact: {
            1: ["Id", "int32"], 2: ["FirstName", "string"], 3: ["LastName", "string"], 4: ["Number", "string"],
            5: ["ExtensionNumber", "string"], 6: ["ContactType", "int32"], 7: ["Company", "string"], 24: ["DnType", "int32"]
        },
        DateTime: {
            1: ["Year", "int32"], 2: ["Month", "int32"], 3: ["Day", "int32"], 4: ["Hour", "int32"], 5: ["Minute", "int32"], 6: ["Second", "int32"]
        }
    };

    var MESSAGE_IDS = { GetMyInfo: 102, GetFile: 105, GetCallHistory: 106, GetVoiceMails: 565 };
    var CALL_TYPES = { 0: "all", 1: "missed", 2: "received", 3: "outgoing" };
    var VOICEMAIL_FOLDER = 0;

    // -- wire format ------------------------------------------------------------

    function Writer() { this.bytes = []; }
    Writer.prototype.varint = function (value) {
        // Non-negative up to 2^53; negative int32 as 10-byte two's complement.
        if (value < 0) {
            var lo = value >>> 0;
            for (var i = 0; i < 4; i += 1) { this.bytes.push((lo & 0x7f) | 0x80); lo >>>= 7; }
            this.bytes.push((lo & 0x0f) | 0x70 | 0x80);
            for (var j = 0; j < 4; j += 1) this.bytes.push(0xff);
            this.bytes.push(0x01);
            return;
        }
        while (value > 0x7f) {
            this.bytes.push((value % 128) | 0x80);
            value = Math.floor(value / 128);
        }
        this.bytes.push(value);
    };
    Writer.prototype.tag = function (num, wire) { this.varint(num * 8 + wire); };
    Writer.prototype.raw = function (bytes) { for (var i = 0; i < bytes.length; i += 1) this.bytes.push(bytes[i]); };

    function utf8Encode(text) {
        return typeof TextEncoder === "function" ? new TextEncoder().encode(String(text)) : Buffer.from(String(text), "utf8");
    }

    function utf8Decode(bytes) {
        return typeof TextDecoder === "function" ? new TextDecoder("utf-8").decode(bytes) : Buffer.from(bytes).toString("utf8");
    }

    function encodeMessage(type, obj, writer) {
        writer = writer || new Writer();
        var schema = SCHEMA[type];
        if (!schema) throw new Error("unknown message " + type);
        Object.keys(schema).map(Number).sort(function (a, b) { return a - b; }).forEach(function (num) {
            var spec = schema[num];
            var value = obj[spec[0]];
            if (value === undefined || value === null) return;
            (spec[2] ? value : [value]).forEach(function (item) { encodeField(writer, num, spec[1], item); });
        });
        return writer;
    }

    function encodeField(writer, num, type, value) {
        switch (type) {
        case "int32": case "uint32": case "int64":
            writer.tag(num, 0); writer.varint(Number(value)); break;
        case "bool":
            writer.tag(num, 0); writer.varint(value ? 1 : 0); break;
        case "string": case "bytes":
            var bytes = type === "string" ? utf8Encode(value) : value;
            writer.tag(num, 2); writer.varint(bytes.length); writer.raw(bytes); break;
        default:
            var inner = encodeMessage(type, value).bytes;
            writer.tag(num, 2); writer.varint(inner.length); writer.raw(inner);
        }
    }

    function Reader(bytes, start, end) { this.buf = bytes; this.pos = start || 0; this.end = end === undefined ? bytes.length : end; }
    Reader.prototype.varint = function () {
        var lo = 0, hi = 0, shift = 0, b;
        do {
            if (this.pos >= this.end) throw new Error("truncated varint");
            b = this.buf[this.pos++];
            if (shift < 28) lo |= (b & 0x7f) << shift;
            else if (shift === 28) { lo |= (b & 0x0f) << 28; hi |= (b & 0x7f) >> 4; }
            else hi |= (b & 0x7f) << (shift - 32);
            shift += 7;
        } while (b & 0x80);
        return { lo: lo >>> 0, hi: hi >>> 0 };
    };
    Reader.prototype.skip = function (wire) {
        if (wire === 0) this.varint();
        else if (wire === 1) this.pos += 8;
        else if (wire === 2) { var n = this.varint().lo; this.pos += n; }
        else if (wire === 5) this.pos += 4;
        else throw new Error("unsupported wire type " + wire);
    };

    function decodeMessage(type, bytes, start, end) {
        var schema = SCHEMA[type] || {};
        var reader = new Reader(bytes, start, end);
        var out = {};
        while (reader.pos < reader.end) {
            var key = reader.varint().lo;
            var num = key >>> 3;
            var wire = key & 7;
            var spec = schema[num];
            if (!spec) { reader.skip(wire); continue; }
            var value;
            if (wire === 0) {
                var v = reader.varint();
                if (spec[1] === "bool") value = v.lo !== 0;
                else if (spec[1] === "int32") value = v.lo | 0;
                else if (spec[1] === "int64") value = v.hi * 4294967296 + v.lo;
                else value = v.lo;
            } else if (wire === 2) {
                var len = reader.varint().lo;
                var from = reader.pos;
                reader.pos += len;
                if (spec[1] === "string") value = utf8Decode(bytes.subarray(from, from + len));
                else if (spec[1] === "bytes") value = bytes.subarray(from, from + len);
                else value = decodeMessage(spec[1], bytes, from, from + len);
            } else {
                reader.skip(wire);
                continue;
            }
            if (spec[2]) (out[spec[0]] = out[spec[0]] || []).push(value);
            else out[spec[0]] = value;
        }
        return out;
    }

    // -- requests ---------------------------------------------------------------

    function request(name, body) {
        var message = { MessageId: MESSAGE_IDS[name] };
        message[name] = body || {};
        return Uint8Array.from(encodeMessage("GenericMessage", message).bytes);
    }

    function myInfoRequest() { return request("GetMyInfo", {}); }

    function callHistoryRequest(extension, limit, offset) {
        return request("GetCallHistory", { CallType: 0, DnOwner: String(extension), RecordLimit: limit || 100, RecordOffset: offset || 0, Search: "" });
    }

    function voicemailFileRequest(voicemail) {
        return request("GetFile", { Folder: VOICEMAIL_FOLDER, FileName: voicemail.filename, ItemId: Number(voicemail.id) });
    }

    function decodeResponse(bytes) {
        return decodeMessage("GenericMessage", bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes));
    }

    // -- records ----------------------------------------------------------------

    function isoTime(dt) {
        if (!dt || !dt.Year) return "";
        return new Date(Date.UTC(dt.Year, (dt.Month || 1) - 1, dt.Day || 1, dt.Hour || 0, dt.Minute || 0, dt.Second || 0)).toISOString();
    }

    function contactName(contact) {
        if (!contact) return "";
        return [contact.FirstName, contact.LastName].filter(Boolean).join(" ").trim() || contact.Company || "";
    }

    function voicemailRecord(vm) {
        return {
            id: vm.Id,
            filename: vm.Filename || "",
            caller_number: vm.CallerId || "",
            caller_name: vm.CallerName || contactName(vm.CallerContact),
            caller_company: vm.CallerContact && vm.CallerContact.Company || "",
            received_at: isoTime(vm.ReceivedAt),
            duration_seconds: Math.round((vm.Duration || 0) / 1000),
            is_new: Boolean(vm.IsNew),
            transcription: vm.Transcription || "",
            heard_by: vm.HeardBy || "",
            group_box: vm.GroupBox || ""
        };
    }

    function myInfoRecord(info) {
        info = info || {};
        var box = info.VoiceMailBox || {};
        return {
            extension: info.Number || "",
            name: [info.FirstName, info.LastName].filter(Boolean).join(" "),
            voicemails: (box.Items || []).map(voicemailRecord)
        };
    }

    // One call: the owner's leg and the other party, with times and outcome.
    function callRecord(record, owner) {
        var parties = (record.connections && record.connections.parties || []).filter(function (p) { return p.PartyDN !== "MakeCall"; });
        var mine = parties.filter(function (p) { return p.PartyDN === owner; });
        var others = parties.filter(function (p) { return p.PartyDN !== owner; });
        var first = parties[0] || {};
        var other = others[0] || {};
        var start = isoTime(first.StartTime);
        var connected = parties.map(function (p) { return isoTime(p.ConnectedAt); }).filter(Boolean).sort()[0] || "";
        var ended = parties.map(function (p) { return isoTime(p.EndedAt); }).filter(Boolean).sort().pop() || "";
        var callType = (mine[0] || first).CallType;
        var outgoing = first.PartyDN === owner;
        return {
            id: record.Id,
            started_at: start,
            answered_at: connected,
            ended_at: ended,
            duration_seconds: connected && ended ? Math.max(0, Math.round((Date.parse(ended) - Date.parse(connected)) / 1000)) : 0,
            direction: outgoing ? "outgoing" : "incoming",
            outcome: connected ? "answered" : (outgoing ? "not answered" : "missed"),
            call_type: CALL_TYPES[callType] || String(callType == null ? "" : callType),
            other_number: other.PartyCallerId || other.PartyDN || "",
            other_name: other.PartyDNName || contactName(other.PartyContact),
            other_extension: other.PartyDNType === 0 ? other.PartyDN || "" : "",
            via: other.ViaDNName || other.ViaDN || "",
            parties: parties.map(function (p) {
                return {
                    dn: p.PartyDN || "", name: p.PartyDNName || contactName(p.PartyContact), caller_id: p.PartyCallerId || "",
                    dn_type: p.PartyDNType, started_at: isoTime(p.StartTime), connected_at: isoTime(p.ConnectedAt), ended_at: isoTime(p.EndedAt)
                };
            })
        };
    }

    function base64(bytes) {
        var out = "";
        for (var i = 0; i < bytes.length; i += 0x8000) {
            out += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
        }
        return typeof btoa === "function" ? btoa(out) : Buffer.from(out, "binary").toString("base64");
    }

    return {
        ENDPOINT: ENDPOINT,
        SCHEMA: SCHEMA,
        encodeMessage: function (type, obj) { return Uint8Array.from(encodeMessage(type, obj).bytes); },
        decodeMessage: decodeMessage,
        myInfoRequest: myInfoRequest,
        callHistoryRequest: callHistoryRequest,
        voicemailFileRequest: voicemailFileRequest,
        decodeResponse: decodeResponse,
        myInfoRecord: myInfoRecord,
        voicemailRecord: voicemailRecord,
        callRecord: callRecord,
        isoTime: isoTime,
        base64: base64
    };
});
