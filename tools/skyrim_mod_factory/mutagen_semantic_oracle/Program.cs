using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Mutagen.Bethesda;
using Mutagen.Bethesda.Assets;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Plugins.Assets;
using Mutagen.Bethesda.Plugins.Records;
using Mutagen.Bethesda.Skyrim;

if (args.Length < 2)
{
    Console.Error.WriteLine("usage: MutagenSemanticOracle <plugin-path> <output-json> [SkyrimSE|SkyrimLE|SkyrimVR]");
    return 2;
}

var pluginPath = Path.GetFullPath(args[0]);
var outputPath = Path.GetFullPath(args[1]);
var release = args.Length >= 3
    ? Enum.Parse<SkyrimRelease>(args[2], ignoreCase: true)
    : SkyrimRelease.SkyrimSE;

if (!File.Exists(pluginPath))
{
    Console.Error.WriteLine($"plugin not found: {pluginPath}");
    return 2;
}

using var mod = SkyrimMod.CreateFromBinaryOverlay(pluginPath, release);
var records = new List<object>();

foreach (var record in mod.EnumerateMajorRecords().OrderBy(r => r.FormKey.ToString(), StringComparer.Ordinal))
{
    var getterInterface = record.GetType().GetInterfaces()
        .Where(t => typeof(IMajorRecordGetter).IsAssignableFrom(t))
        .Select(t => new
        {
            Type = t,
            Attr = t.GetCustomAttribute<AssociatedRecordTypesAttribute>()
        })
        .FirstOrDefault(x => x.Attr is not null && x.Attr.Types.Length > 0);

    var signature = getterInterface?.Attr?.Types[0].ToString();
    if (string.IsNullOrWhiteSpace(signature) || signature.Length != 4)
    {
        throw new InvalidOperationException(
            $"Could not resolve four-character record signature for {record.FormKey} ({record.GetType().FullName})"
        );
    }

    var assets = record
        .EnumerateAssetLinks(AssetLinkQuery.Listed)
        .Select(x => x.DataRelativePath.Path.Replace('/', '\\'))
        .Where(x => !string.IsNullOrWhiteSpace(x))
        .Distinct(StringComparer.OrdinalIgnoreCase)
        .OrderBy(x => x, StringComparer.OrdinalIgnoreCase)
        .ToArray();

    records.Add(new
    {
        form_key = record.FormKey.ToString(),
        signature,
        editor_id = record.EditorID,
        asset_paths = assets,
        fields = new Dictionary<string, object?>
        {
            ["_mutagen"] = new
            {
                getter_interface = getterInterface?.Type.FullName,
                runtime_type = record.GetType().FullName
            }
        }
    });
}

var infoVersion = typeof(SkyrimMod).Assembly
    .GetCustomAttribute<AssemblyInformationalVersionAttribute>()
    ?.InformationalVersion;

var document = new
{
    schema_version = "skyrim-semantic-plugin-v1",
    plugin = new
    {
        mod_key = mod.ModKey.ToString(),
        game_release = release.ToString()
    },
    records,
    provenance = new
    {
        producer = "mutagen-semantic-oracle",
        producer_version = "1.0",
        mutagen_version = infoVersion,
        form_key_mode = "mutagen-formkey-string",
        canonical_cross_load_order_form_keys = true,
        coverage = new
        {
            records_emitted = records.Count,
            semantic_fields = new[] { "editor_id", "asset_paths" },
            omissions = new[]
            {
                "generic field-tree semantics are not emitted yet",
                "VMAD/script semantics are not emitted yet",
                "record flags are not emitted yet"
            }
        }
    }
};

Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);
await File.WriteAllTextAsync(
    outputPath,
    JsonSerializer.Serialize(
        document,
        new JsonSerializerOptions
        {
            WriteIndented = true,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        }
    ) + Environment.NewLine
);

Console.WriteLine(outputPath);
return 0;
