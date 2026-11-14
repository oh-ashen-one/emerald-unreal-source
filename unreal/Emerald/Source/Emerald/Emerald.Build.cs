using UnrealBuildTool;
public class Emerald : ModuleRules
{
    public Emerald(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] {
            "Core", "CoreUObject", "Engine", "InputCore", "ApplicationCore", "Json", "JsonUtilities", "RenderCore", "RHI"
        });
    }
}
