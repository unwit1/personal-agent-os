import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location(
    "render_fomod",
    ROOT/"render_fomod.py",
)
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def intent():
    return {
        "schema_version":"skyrim-fomod-intent-v1",
        "metadata":{
            "name":"Fixture Mod",
            "author":"Fixture Author",
            "version":"1.2.3",
            "machine_version":"1.2.3",
            "description":"Fixture installer",
            "website":"https://example.com/mod",
        },
        "module":{
            "name":"Fixture Mod Installer",
            "image":"fomod/header.png",
            "dependencies":{
                "kind":"file",
                "file":"Skyrim.esm",
                "state":"Active",
            },
            "required_files":[
                {
                    "kind":"folder",
                    "source":"core",
                    "destination":"",
                }
            ],
            "steps_order":"Explicit",
            "steps":[{
                "name":"Choose Variant",
                "groups":[{
                    "name":"Variant",
                    "type":"SelectExactlyOne",
                    "order":"Explicit",
                    "options":[
                        {
                            "name":"Standard",
                            "description":"Standard files",
                            "type":"Recommended",
                            "files":[{
                                "kind":"folder",
                                "source":"variants/standard",
                                "destination":"",
                            }],
                            "flags":[{"name":"variant","value":"standard"}],
                        },
                        {
                            "name":"Alternate",
                            "description":"Alternate files",
                            "type":"Optional",
                            "files":[{
                                "kind":"folder",
                                "source":"variants/alternate",
                                "destination":"",
                            }],
                            "flags":[{"name":"variant","value":"alternate"}],
                        },
                    ],
                }],
            }],
            "conditional_installs":[{
                "dependencies":{
                    "kind":"flag",
                    "flag":"variant",
                    "value":"alternate",
                },
                "files":[{
                    "kind":"file",
                    "source":"conditional/alternate.ini",
                    "destination":"SKSE/Plugins/alternate.ini",
                    "priority":10,
                }],
            }],
        },
    }

class RenderFomodTests(unittest.TestCase):
    def make_package(self,root:Path):
        (root/"fomod").mkdir()
        (root/"fomod"/"header.png").write_bytes(b"image")
        (root/"core").mkdir()
        (root/"core"/"base.txt").write_text("base",encoding="utf-8")
        (root/"variants"/"standard").mkdir(parents=True)
        (root/"variants"/"alternate").mkdir(parents=True)
        (root/"conditional").mkdir()
        (root/"conditional"/"alternate.ini").write_text("x=1",encoding="utf-8")

    def test_render_validates_against_vendored_xsd(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.make_package(root)
            info,module=MOD.render(intent(),package_root=root)
            self.assertEqual(MOD.validate_xsd(module),[])
            info_root=ET.fromstring(info)
            module_root=ET.fromstring(module)
            self.assertEqual(info_root.findtext("Name"),"Fixture Mod")
            self.assertEqual(module_root.findtext("moduleName"),"Fixture Mod Installer")
            self.assertEqual(
                [x.tag for x in list(module_root)],
                [
                    "moduleName","moduleImage","moduleDependencies",
                    "requiredInstallFiles","installSteps",
                    "conditionalFileInstalls",
                ],
            )

    def test_dependency_leaf_is_wrapped_as_composite(self):
        _,module=MOD.render(intent())
        root=ET.fromstring(module)
        deps=root.find("moduleDependencies")
        self.assertIsNotNone(deps)
        self.assertEqual(deps.attrib["operator"],"And")
        fd=deps.find("fileDependency")
        self.assertEqual(fd.attrib,{"file":"Skyrim.esm","state":"Active"})

    def test_package_source_validation_fails_missing_reference(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.make_package(root)
            value=intent()
            value["module"]["required_files"][0]["source"]="missing"
            with self.assertRaisesRegex(ValueError,"does not exist"):
                MOD.render(value,package_root=root)

    def test_path_traversal_is_rejected(self):
        value=intent()
        value["module"]["required_files"][0]["source"]="../outside"
        with self.assertRaises(ValueError):
            MOD.render(value)

    def test_exactly_one_rejects_multiple_recommended_defaults(self):
        value=intent()
        value["module"]["steps"][0]["groups"][0]["options"][1]["type"]="Recommended"
        with self.assertRaisesRegex(ValueError,"Recommended defaults"):
            MOD.render(value)

    def test_option_requires_files_or_flags(self):
        value=intent()
        option=value["module"]["steps"][0]["groups"][0]["options"][0]
        option.pop("files")
        option.pop("flags")
        with self.assertRaisesRegex(ValueError,"intent failed schema"):
            MOD.render(value)

    def test_nested_dependency_renders_and_validates(self):
        value=intent()
        value["module"]["dependencies"]={
            "kind":"group",
            "operator":"And",
            "items":[
                {"kind":"file","file":"Skyrim.esm","state":"Active"},
                {
                    "kind":"group",
                    "operator":"Or",
                    "items":[
                        {"kind":"file","file":"A.esp","state":"Active"},
                        {"kind":"file","file":"B.esp","state":"Active"},
                    ],
                },
            ],
        }
        _,module=MOD.render(value)
        self.assertEqual(MOD.validate_xsd(module),[])
        root=ET.fromstring(module)
        nested=root.find("moduleDependencies/dependencies")
        self.assertEqual(nested.attrib["operator"],"Or")
        self.assertEqual(len(nested.findall("fileDependency")),2)

if __name__=="__main__":
    unittest.main()
