using UnrealBuildTool;
using System.Collections.Generic;
public class EmeraldTarget : TargetRules
{
    public EmeraldTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V7;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("Emerald");
    }
}
