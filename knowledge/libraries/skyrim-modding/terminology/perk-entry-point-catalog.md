# Skyrim Modding Terminology — Perk Entry Point Catalog

Imported: 2026-09-24
Status: reverse-engineered finite-engine catalog pass

Perk Entry Points are predefined engine hook locations where PERK entries can query conditions and alter calculations/actions. Current CommonLibSSE-derived enum evidence exposes 92 Skyrim entry points numbered 0–91.

## Entry points (engine enum)

### CalculateWeaponDamage
Modify weapon damage calculation.

### CalculateMyCriticalHitChance
Modify attacker's critical-hit chance.

### CalculateMyCriticalHitDamage
Modify attacker's critical-hit damage.

### CalculateMineExplodeChance
Modify mine/trap explosion chance.

### AdjustLimbDamage
Legacy-named engine entry point retained in Skyrim enum; exact Skyrim applicability should be tested before authoring.

### AdjustBookSkillPoints
Modify skill points gained from reading skill book.

### ModRecoveredHealth
Modify recovered Health.

### GetShouldAttack
Influence whether actor should attack.

### ModBuyPrices
Modify player purchase price.

### AddLeveledListOnDeath
Add leveled-list content when target dies.

### GetMaxCarryWeight
Modify carry-weight maximum.

### ModAddictionChance
Legacy/engine entry point; Skyrim applicability is limited/unclear.

### ModAddictionDuration
Legacy/engine entry point; Skyrim applicability limited/unclear.

### ModPositiveChemDuration
Legacy-named engine entry point retained from Bethesda lineage; do not assume Fallout semantics in Skyrim.

### Activate
Perk-mediated activation action/choice behavior.

### IgnoreRunningDuringDetection
Modify detection penalty/logic for running.

### IgnoreBrokenLock
Alter lock behavior around broken lock state.

### ModEnemyCriticalHitChance
Modify enemy critical-hit chance.

### ModSneakAttackMult
Modify sneak-attack multiplier.

### ModMaxPlaceableMines
Legacy-named placement limit entry retained by enum; validate Skyrim use.

### ModBowZoom
Modify bow zoom.

### ModRecoverArrowChance
Modify chance arrows are recoverable.

### ModSkillUse
Modify skill-use progression.

### ModTelekinesisDistance
Modify telekinesis range.

### ModTelekinesisDamageMult
Modify telekinesis damage multiplier.

### ModTelekinesisDamage
Modify telekinesis damage.

### ModBashingDamage
Modify bash damage.

### ModPowerAttackStamina
Modify power-attack stamina cost.

### ModPowerAttackDamage
Modify power-attack damage.

### ModSpellMagnitude
Modify outgoing spell/effect magnitude.

### ModSpellDuration
Modify outgoing spell/effect duration.

### ModSecondaryValueWeight
Modify secondary ActorValue weighting.

### ModArmorWeight
Modify armor weight contribution.

### ModIncomingStagger
Modify stagger received.

### ModTargetStagger
Modify stagger dealt to target.

### ModAttackDamage
Modify outgoing attack damage.

### ModIncomingDamage
Modify incoming damage before application.

### ModTargetDamageResistance
Modify target damage resistance.

### ModSpellCost
Modify spell magicka cost.

### ModPercentBlocked
Modify blocked-damage percentage.

### ModShieldDeflectArrowChance
Modify shield arrow-deflection chance.

### ModIncomingSpellMagnitude
Modify incoming magic magnitude.

### ModIncomingSpellDuration
Modify incoming magic duration.

### ModPlayerIntimidation
Modify intimidation calculation.

### ModPlayerReputation
Modify reputation-related calculation.

### ModFavorPoints
Modify favor point changes.

### ModBribeAmount
Modify bribe amount.

### ModDetectionLight
Modify light contribution to detection.

### ModDetectionMovement
Modify movement contribution to detection.

### ModSoulGemRecharge
Modify weapon recharge/soul-gem contribution.

### SetSweepAttack
Enable/alter sweep/multi-target attack behavior.

### ApplyCombatHitSpell
Apply configured spell on combat hit.

### ApplyBashingSpell
Apply configured spell on bash.

### ApplyReanimateSpell
Apply configured spell in reanimation context.

### SetBooleanGraphVariable
Set animation graph bool through perk entry.

### ModSpellCastingSoundEvent
Modify spell casting sound event.

### ModPickpocketChance
Modify pickpocket chance.

### ModDetectionSneakSkill
Modify Sneak skill contribution to detection.

### ModFallingDamage
Modify fall damage.

### ModLockpickSweetSpot
Modify lockpick sweet-spot size.

### ModSellPrices
Modify player sale price.

### CanPickpocketEquippedItem
Allow/deny stealing equipped items.

### ModLockpickLevelAllowed
Modify lock difficulty player is permitted to pick.

### SetLockpickStartingArc
Change initial lockpick angle/arc.

### SetProgressionPicking
Influence lockpicking progression behavior.

### MakeLockpicksUnbreakable
Prevent lockpick breakage.

### ModAlchemyEffectiveness
Modify potion/poison effectiveness.

### ApplyWeaponSwingSpell
Apply spell during weapon-swing event.

### ModCommandedActorLimit
Modify maximum commanded/summoned actor count.

### ApplySneakingSpell
Apply spell in sneak state/context.

### ModPlayerMagicSlowdown
Modify player movement slowdown during magic use.

### ModWardMagickaAbsorptionPct
Modify ward magicka absorption percentage.

### ModInitialIngredientEffectsLearned
Modify number of ingredient effects revealed initially.

### PurifyAlchemyIngredients
Alter ingredient impurity/negative-effect handling.

### FilterActivation
Filter/intercept activation.

### CanDualCastSpell
Allow/deny dual casting.

### ModTemperingHealth
Modify tempering improvement/health.

### ModEnchantmentPower
Modify enchanting strength.

### ModSoulPctCapturedToWeapon
Modify soul percentage transferred for weapon recharge.

### ModSoulGemEnchanting
Modify soul-gem contribution to enchanting.

### ModNumberAppliedEnchantmentsAllowed
Modify count of enchantments allowed on one item.

### SetActivateLabel
Change activation prompt text.

### ModShoutOK
Modify whether shout action is permitted.

### ModPoisonDoseCount
Modify number of poison applications/doses.

### ShouldApplyPlacedItem
Influence whether placed-item effect applies.

### ModArmorRating
Modify armor rating.

### ModLockpickingCrimeChance
Modify lockpicking crime chance.

### ModIngredientsHarvested
Modify harvest yield.

### ModSpellRange_TargetLoc
Modify target-location spell range.

### ModPotionsCreated
Modify count of potions created.

### ModLockpickingKeyRewardChance
Modify chance of key reward during lockpicking-related behavior.

### AllowMountActor
Allow/deny mounting actor.

## Perk entry structure

### Perk owner
Actor whose perks are being evaluated.

### Entry-point arguments
Context supplied by engine such as target, weapon, spell, item, attacker or furniture.

### Entry-point condition
Condition list evaluated against owner/context.

### Function
Operation applied by perk entry: multiply, add, set, apply spell, activate choice, etc.

### Priority
Order in which multiple relevant perk entries execute.

### Entry Point Function
Specific function type associated with one entry, not to be confused with the enum/hook itself.

### Ability entry
PERK entry granting an Ability rather than modifying a code entry point.

### Quest entry
PERK entry starting/advancing quest rather than modifying calculation.

## Perk Entry Point Extender / PEPE

### PEPE
SKSE framework exposing perk Entry Points to Papyrus/native APIs and enabling categorized/reusable pseudo-entry-point groups.

### Entry-point categorization
PEPE uses categories to selectively execute only entries associated with requested category.

### GROUP__ keyword
Modern PEPE grouping convention using keyword/category rather than only EditorID naming.

### Entry handle
Supplies context values that ordinary Papyrus calls cannot naturally provide to entry-point condition evaluation.

### Secondary argument
PEPE can provide second context target for paired condition evaluation.

### ExtraData-aware evaluation
Modern PEPE can attach InventoryEntryData/ExtraData context so conditions can inspect instance-level state such as tempering/stolen/alias-added keywords.

### EPValue
Optional generated ActorValue channel used by newer PEPE features to pass numeric data into entry evaluation.

### ReverseOrder
PEPE flag executing matching entry set in reverse priority order.

### Native API
Other SKSE plugins can invoke/register extended entry-point behavior.

## Diagnostic rules

1. Perk Entry Points operate inside engine calculations before/around events; they can alter outcomes that Papyrus OnHit sees only afterward.
2. Multiple perks can stack/order; inspect every perk granting same entry point.
3. Base-form conditions cannot see inventory-instance ExtraData unless framework explicitly supplies it.
4. Some enum names are Bethesda lineage artifacts; do not infer Fallout behavior exists in Skyrim without evidence.
5. Apply-spell entry points interact with Scrambled Bugs/multi-return fixes; version compatibility matters.
6. Perk entry-point effects are not ordinary MagicEffects and may not appear in Active Effects UI.
7. When debugging numeric gameplay changes, inspect perks/entry points before assuming scripts changed ActorValues directly.

## Sources

- CommonLibSSE-NG-derived ENTRY_POINT enum: https://commonlibsse-ng-docs-rs.netlify.app/src/commonlibsse_ng/re/b/bgsentrypoint.rs
- Perk Entry Point Extender: https://www.nexusmods.com/skyrimspecialedition/mods/91192
- PEPE source: https://github.com/NoahBoddie/perk-entry-point-extender
- CK Wiki OnHit discussion referencing Mod Incoming Damage timing: https://ck.uesp.net/wiki/Talk:OnHit_-_ObjectReference

## Dated snapshot

Perk Entry Point Extender 2.3.7.0 was current on 2026-09-24, updated 2026-08-30. The 92-entry engine enum cited here is reverse-engineered library evidence and should be version-scoped if Bethesda changes executable behavior.
