using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins.Assets;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Plugins.Records.Mapping;
using Mutagen.Bethesda.Skyrim;

static void Usage()
{
    Console.Error.WriteLine(
        "Usage: mutagen-semantic-export <plugin> <output.json> [SkyrimSE|SkyrimLE|SkyrimVR]");
}

if (args.Length < 2 || args.Length > 3)
{
    Usage();
    return 64;
}

var pluginPath = Path.GetFullPath(args[0]);
var outputPath = Path.GetFullPath(args[1]);
if (!File.Exists(pluginPath))
{
    Console.Error.WriteLine($"Plugin not found: {pluginPath}");
    return 66;
}

var release = args.Length == 3
    ? Enum.Parse<SkyrimRelease>(args[2], ignoreCase: true)
    : SkyrimRelease.SkyrimSE;

static string Signature(IMajorRecordGetter record)
{
    var attributes = record.GetType()
        .GetInterfaces()
        .SelectMany(t => t.GetCustomAttributes<AssociatedRecordTypesAttribute>(inherit: true))
        .ToArray();
    var types = attributes
        .SelectMany(a => a.Types)
        .Select(t => t.ToString())
        .Where(x => x.Length == 4)
        .Distinct(StringComparer.Ordinal)
        .ToArray();
    if (types.Length != 1)
    {
        throw new InvalidOperationException(
            $"Expected exactly one four-character record signature for {record.GetType().FullName}; " +
            $"found [{string.Join(", ", types)}]");
    }
    return types[0];
}

static string FileSha256(string path)
{
    using var stream = File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
}

using var mod = SkyrimMod.CreateFromBinaryOverlay(pluginPath, release);

var records = mod.EnumerateMajorRecords()
    .Select(record =>
    {
        var assets = record
            .EnumerateAssetLinks(AssetLinkQuery.Listed, linkCache: null, assetType: null)
            .Where(x => !x.IsNull)
            .Select(x => x.DataRelativePath.Path.Replace('/', '\\'))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(x => x, StringComparer.OrdinalIgnoreCase)
            .ToArray();

        return new Dictionary<string, object?>
        {
            ["form_key"] = record.FormKey.ToString(),
            ["signature"] = Signature(record),
            ["editor_id"] = record.EditorID,
            ["flags"] = new Dictionary<string, object?>
            {
                ["raw"] = record.MajorRecordFlagsRaw,
            },
            ["fields"] = new Dictionary<string, object?>
            {
                ["_mutagen"] = new Dictionary<string, object?>
                {
                    ["runtime_type"] = record.GetType().FullName,
                    ["version_control"] = record.VersionControl,
                },
            },
            ["asset_paths"] = assets,
        };
    })
    .OrderBy(r => (string)r["signature"]!, StringComparer.Ordinal)
    .ThenBy(r => (string)r["form_key"]!, StringComparer.Ordinal)
    .ToArray();

var document = new Dictionary<string, object?>
{
    ["schema_version"] = "skyrim-semantic-plugin-v1",
    ["plugin"] = new Dictionary<string, object?>
    {
        ["mod_key"] = mod.ModKey.ToString(),
        ["game_release"] = release.ToString(),
        ["header"] = new Dictionary<string, object?>
        {
            ["master_references"] = mod.ModHeader.MasterReferences
                .Select(x => x.Master.ToString())
                .ToArray(),
        },
    },
    ["records"] = records,
    ["provenance"] = new Dictionary<string, object?>
    {
        ["producer"] = "mutagen-semantic-export",
        ["producer_version"] = "1.0",
        ["mutagen_version"] = typeof(SkyrimMod).Assembly.GetName().Version?.ToString(),
        ["created_at"] = DateTimeOffset.UtcNow.ToString("O"),
        ["source_plugin_sha256"] = FileSha256(pluginPath),
        ["form_key_mode"] = "mutagen-formkey-string",
        ["canonical_cross_load_order_form_keys"] = true,
        ["coverage"] = new Dictionary<string, object?>
        {
            ["records_emitted"] = records.Length,
            ["semantic_fields"] = new[] { "editor_id", "asset_paths" },
            ["omissions"] = new[]
            {
                "only cross-producer semantic fields are declared comparable in v1",
                "record-specific typed fields remain available to future per-signature emitters",
                "VMAD normalization is not yet emitted by this producer",
            },
        },
    },
};

var options = new JsonSerializerOptions
{
    WriteIndented = true,
    PropertyNamingPolicy = null,
};
Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);
await File.WriteAllTextAsync(
    outputPath,
    JsonSerializer.Serialize(document, options) + Environment.NewLine);
Console.WriteLine(outputPath);
return 0;
