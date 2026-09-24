# xEdit Skyrim Record Schema Source Map

Updated: 2026-09-24
Status: canonical ingestion source map

The TES5Edit/meta `UESPWiki` directory currently exposes **131 schema/support files**, of which **127** follow the `<signature>Def.wiki` record-definition naming pattern. These files are reverse-engineered technical documentation and should be treated as structured evidence for record/subrecord layouts, not as an official Bethesda specification.

Canonical upstream directory:
https://github.com/TES5Edit/meta/tree/master/UESPWiki

## Ingestion policy

For each record schema, Agent OS should eventually store:
- record signature and human name;
- common fields;
- every important subrecord signature;
- value type/size where documented;
- flags/enums;
- ordering/repetition semantics;
- references to other form types;
- conflict-resolution implications;
- fields unsafe to merge mechanically;
- version/runtime notes;
- source revision/date.

Do not automatically copy raw schema tables wholesale into the knowledge base. Normalize field semantics and preserve a link to the exact upstream definition.

## Actors, AI, quests, dialogue

| Signature | xEdit schema source |
|---|---|
| `ACHR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ACHRDef.wiki |
| `AVIF` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/AVIFDef.wiki |
| `CLAS` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CLASDef.wiki |
| `CSTY` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CSTYDef.wiki |
| `DIAL` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/DIALDef.wiki |
| `DLBR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/DLBRDef.wiki |
| `DLVW` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/DLVWDef.wiki |
| `FACT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/FACTDef.wiki |
| `INFO` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/INFODef.wiki |
| `NPC_` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/NPC_Def.wiki |
| `PACK` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/PACKDef.wiki |
| `PERK` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/PERKDef.wiki |
| `QUST` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/QUSTDef.wiki |
| `RACE` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/RACEDef.wiki |
| `RELA` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/RELADef.wiki |
| `SCEN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SCENDef.wiki |
| `VTYP` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/VTYPDef.wiki |

## Magic, items, crafting

| Signature | xEdit schema source |
|---|---|
| `ALCH` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ALCHDef.wiki |
| `AMMO` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/AMMODef.wiki |
| `APPA` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/APPADef.wiki |
| `ARMA` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ARMADef.wiki |
| `ARMO` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ARMODef.wiki |
| `BOOK` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/BOOKDef.wiki |
| `COBJ` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/COBJDef.wiki |
| `ENCH` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ENCHDef.wiki |
| `EYES` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/EYESDef.wiki |
| `HDPT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/HDPTDef.wiki |
| `INGR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/INGRDef.wiki |
| `KEYM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/KEYMDef.wiki |
| `MGEF` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MGEFDef.wiki |
| `MISC` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MISCDef.wiki |
| `OTFT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/OTFTDef.wiki |
| `SCRL` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SCRLDef.wiki |
| `SHOU` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SHOUDef.wiki |
| `SLGM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SLGMDef.wiki |
| `SPEL` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SPELDef.wiki |
| `WEAP` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/WEAPDef.wiki |
| `WOOP` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/WOOPDef.wiki |

## World, cells, landscape, navigation

| Signature | xEdit schema source |
|---|---|
| `CELL` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CELLDef.wiki |
| `CLMT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CLMTDef.wiki |
| `COLL` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/COLLDef.wiki |
| `ECZN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ECZNDef.wiki |
| `GRAS` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/GRASDef.wiki |
| `LAND` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LANDDef.wiki |
| `LCRT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LCRTDef.wiki |
| `LCTN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LCTNDef.wiki |
| `LTEX` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LTEXDef.wiki |
| `NAVI` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/NAVIDef.wiki |
| `NAVM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/NAVMDef.wiki |
| `NVMI` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/NVMIDef.wiki |
| `NVNM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/NVNMDef.wiki |
| `NVPP` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/NVPPDef.wiki |
| `PGRE` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/PGREDef.wiki |
| `PHZD` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/PHZDDef.wiki |
| `REFR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/REFRDef.wiki |
| `REGN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/REGNDef.wiki |
| `STAT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/STATDef.wiki |
| `TREE` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/TREEDef.wiki |
| `WATR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/WATRDef.wiki |
| `WRLD` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/WRLDDef.wiki |
| `WTHR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/WTHRDef.wiki |

## Audio, visuals, UI/environment

| Signature | xEdit schema source |
|---|---|
| `ADDN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ADDNDef.wiki |
| `ARTO` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ARTODef.wiki |
| `ASPC` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ASPCDef.wiki |
| `CLFM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CLFMDef.wiki |
| `DEBR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/DEBRDef.wiki |
| `DUAL` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/DUALDef.wiki |
| `EFSH` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/EFSHDef.wiki |
| `EXPL` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/EXPLDef.wiki |
| `HAZD` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/HAZDDef.wiki |
| `IMAD` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/IMADDef.wiki |
| `IMGS` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/IMGSDef.wiki |
| `IPCT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/IPCTDef.wiki |
| `IPDS` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/IPDSDef.wiki |
| `LGTM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LGTMDef.wiki |
| `LIGH` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LIGHDef.wiki |
| `LSCR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LSCRDef.wiki |
| `MATO` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MATODef.wiki |
| `MATT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MATTDef.wiki |
| `MESG` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MESGDef.wiki |
| `MSTT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MSTTDef.wiki |
| `MUSC` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MUSCDef.wiki |
| `MUST` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MUSTDef.wiki |
| `REVB` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/REVBDef.wiki |
| `RFCT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/RFCTDef.wiki |
| `SNCT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SNCTDef.wiki |
| `SNDR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SNDRDef.wiki |
| `SOPM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SOPMDef.wiki |
| `SOUN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SOUNDef.wiki |
| `SPGD` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SPGDDef.wiki |
| `TACT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/TACTDef.wiki |
| `TXST` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/TXSTDef.wiki |

## Data primitives and systems

| Signature | xEdit schema source |
|---|---|
| `AACT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/AACTDef.wiki |
| `ACTI` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ACTIDef.wiki |
| `ANIO` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/ANIODef.wiki |
| `BPTD` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/BPTDDef.wiki |
| `CAMS` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CAMSDef.wiki |
| `CONT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CONTDef.wiki |
| `CPTH` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/CPTHDef.wiki |
| `DOBJ` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/DOBJDef.wiki |
| `DOOR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/DOORDef.wiki |
| `EQUP` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/EQUPDef.wiki |
| `FLOR` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/FLORDef.wiki |
| `FLST` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/FLSTDef.wiki |
| `FSTP` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/FSTPDef.wiki |
| `FSTS` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/FSTSDef.wiki |
| `FURN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/FURNDef.wiki |
| `GLOB` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/GLOBDef.wiki |
| `GMST` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/GMSTDef.wiki |
| `IDLE` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/IDLEDef.wiki |
| `IDLM` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/IDLMDef.wiki |
| `KYWD` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/KYWDDef.wiki |
| `LVLI` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LVLIDef.wiki |
| `LVLN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LVLNDef.wiki |
| `LVSP` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/LVSPDef.wiki |
| `MOVT` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/MOVTDef.wiki |
| `PROJ` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/PROJDef.wiki |
| `SMBN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SMBNDef.wiki |
| `SMEN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SMENDef.wiki |
| `SMQN` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/SMQNDef.wiki |
| `TES4` | https://github.com/TES5Edit/meta/blob/master/UESPWiki/TES4Def.wiki |

## Additional record definitions

- `ASTP` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/ASTPDef.wiki
- `BOD2` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/BOD2Def.wiki
- `BODT` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/BODTDef.wiki
- `COED` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/COEDDef.wiki
- `OBND` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/OBNDDef.wiki
- `VMAD` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/VMADDef.wiki

## Shared/support schemas

- `CommonFields.wiki` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/CommonFields.wiki
- `DESTFields.wiki` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/DESTFields.wiki
- `MODLFields.wiki` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/MODLFields.wiki
- `MainWikiPage.wiki` — https://github.com/TES5Edit/meta/blob/master/UESPWiki/MainWikiPage.wiki

## High-priority deep-parse order

1. TES4, CommonFields, VMAD
2. REFR, ACHR, CELL, WRLD, LAND
3. NPC_, RACE, ARMO, ARMA
4. QUST, DIAL, INFO, SCEN, PACK
5. MGEF, SPEL, ENCH, PERK
6. LVLI, LVLN, FLST, COBJ
7. WTHR, CLMT, REGN, IMGS, IMAD, LGTM
8. NAVM/NAVI and navmesh support structures
9. WATR/LTEX/TXST/material records
10. audio and visual-effect record families

## Status

This source map closes the discovery portion of the record-schema frontier. Field-by-field normalization remains an incremental structured-ingestion task and should be generated from these sources in batches with provenance.
