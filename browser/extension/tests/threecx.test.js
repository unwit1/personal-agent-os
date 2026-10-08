"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const X = require("../src/lib/threecx-core.js");
const { makeBrowser, sendToContent, makeDom, load, waitFor } = require("./helpers");

const dt = (iso) => {
    const d = new Date(iso);
    return { Year: d.getUTCFullYear(), Month: d.getUTCMonth() + 1, Day: d.getUTCDate(), Hour: d.getUTCHours(), Minute: d.getUTCMinutes(), Second: d.getUTCSeconds() };
};

test("3CX codec: requests match the web client and responses decode into records", () => {
    assert.equal(Buffer.from(X.myInfoRequest()).toString("hex"), "0866b20600");
    const history = X.decodeMessage("GenericMessage", X.callHistoryRequest("901", 100, 0));
    assert.equal(history.MessageId, 106);
    assert.deepEqual({ ...history.GetCallHistory }, { CallType: 0, DnOwner: "901", RecordLimit: 100, RecordOffset: 0, Search: "" });
    const info = X.myInfoRecord(X.decodeResponse(X.encodeMessage("GenericMessage", { MessageId: 201, MyInfo: {
        Number: "901", FirstName: "Test", LastName: "User",
        VoiceMailBox: { Items: [{ Id: 7, Filename: "vm7.wav", CallerId: "5550100123", CallerName: "WIRELESS CALLER",
            ReceivedAt: dt("2026-10-06T15:00:05Z"), Duration: 42000, IsNew: true, Transcription: "Call me back" }] }
    } })).MyInfo);
    assert.equal(info.extension, "901");
    assert.deepEqual(info.voicemails[0], { id: 7, filename: "vm7.wav", caller_number: "5550100123", caller_name: "WIRELESS CALLER",
        caller_company: "", received_at: "2026-10-06T15:00:05.000Z", duration_seconds: 42, is_new: true,
        transcription: "Call me back", heard_by: "", group_box: "" });
    const call = X.callRecord(X.decodeResponse(X.encodeMessage("GenericMessage", { MessageId: 204, CallHistory: { Records: [{ Id: 9, connections: { parties: [
        { PartyDN: "10000", PartyDNType: 1, PartyDNName: "MONHOLLEN COREY", PartyCallerId: "6062907799", StartTime: dt("2026-10-06T14:00:00Z"), EndedAt: dt("2026-10-06T14:00:21Z"), CallType: -1 },
        { PartyDN: "901", PartyDNType: 0, PartyDNName: "Test User", StartTime: dt("2026-10-06T14:00:00Z"), EndedAt: dt("2026-10-06T14:00:21Z"), CallType: 1 }
    ] } }] } })).CallHistory.Records[0], "901");
    assert.equal(call.outcome, "missed");
    assert.equal(call.direction, "incoming");
    assert.equal(call.other_name, "MONHOLLEN COREY");
    assert.equal(call.other_number, "6062907799");
    assert.equal(call.call_type, "missed");
});

test("3CX tab: the web client's session drives a sync of voicemails, audio and calls", async () => {
    const messages = [];
    const browser = makeBrowser({
        onBackgroundMessage: async (message) => {
            messages.push(message);
            if (message.type === "threecx-voicemail") return { ok: true, path: "C:/intake/3cx/voicemails/vm_7.wav" };
            return { ok: true };
        }
    });
    const dom = makeDom(`<!doctype html><html><body><nav><a href="#/chat">Chat</a><a href="#/voicemails">Voicemail <span class="badge">1</span></a></nav></body></html>`,
        "https://rtec.ky.3cx.us:5001/#/people", browser);
    dom.window.wrappedJSObject = dom.window;
    dom.window.exportFunction = (fn) => fn;
    dom.window.TextEncoder = TextEncoder; // as in Firefox content scripts
    dom.window.TextDecoder = TextDecoder;
    const posted = [];
    dom.window.fetch = async (url, init) => {
        const request = X.decodeMessage("GenericMessage", new Uint8Array(init.body));
        posted.push({ url: String(url), session: init.headers.MyPhoneSession, id: request.MessageId });
        let reply = { MessageId: 0 };
        if (request.MessageId === 102) {
            reply = { MessageId: 201, MyInfo: { Number: "901", VoiceMailBox: { Items: [{ Id: 7, Filename: "vm7.wav", CallerId: "5550100123",
                ReceivedAt: dt("2026-10-06T15:00:05Z"), Duration: 42000, IsNew: true }] } } };
        } else if (request.MessageId === 106) {
            reply = { MessageId: 204, CallHistory: { Records: [{ Id: 9, connections: { parties: [
                { PartyDN: "10000", PartyCallerId: "6062907799", StartTime: dt("2026-10-06T14:00:00Z") },
                { PartyDN: "901", StartTime: dt("2026-10-06T14:00:00Z") }] } }] } };
        } else if (request.MessageId === 105) {
            reply = { MessageId: 203, FileResult: { Content: new Uint8Array([82, 73, 70, 70]) } };
        }
        const bytes = X.encodeMessage("GenericMessage", reply);
        return { ok: true, arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) };
    };
    load(dom, ["lib/threecx-core.js", "content/threecx.js"]);
    // The web client sends its own MyPhone request (Angular HttpClient = XHR).
    const xhr = new dom.window.XMLHttpRequest();
    xhr.open("POST", "/MyPhone/MPWebService.asmx");
    xhr.setRequestHeader("MyPhoneSession", "sess-1");
    const result = await sendToContent(browser, { type: "threecx-sync", force: true });
    assert.equal(result.ok, true, JSON.stringify(result));
    assert.deepEqual(posted.map((p) => p.id), [102, 106, 105]);
    assert.ok(posted.every((p) => p.session === "sess-1" && p.url === "/MyPhone/MPWebService.asmx"));
    const audio = messages.find((m) => m.type === "threecx-voicemail");
    assert.equal(audio.audio_base64, Buffer.from("RIFF").toString("base64"));
    const events = messages.find((m) => m.type === "threecx-events").events;
    assert.deepEqual(Array.from(events, (e) => e.event_id), ["3cx:call:9", "3cx:voicemail:7"]);
    assert.equal(events[1].payload.audio_path, "C:/intake/3cx/voicemails/vm_7.wav");
    // Already downloaded: the next sync does not fetch the audio again.
    posted.length = 0;
    await sendToContent(browser, { type: "threecx-sync", force: true });
    assert.deepEqual(posted.map((p) => p.id), [102, 106]);
    dom.window.close();
});
