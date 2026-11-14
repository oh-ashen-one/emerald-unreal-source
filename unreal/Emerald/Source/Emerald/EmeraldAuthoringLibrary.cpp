#include "EmeraldAuthoringLibrary.h"
#if WITH_EDITOR
#include "AssetCompilingManager.h"
#include "Materials/Material.h"
#include "MaterialShared.h"
#include "Misc/App.h"
#include "RenderingThread.h"
#include "RHI.h"
#include "ShaderCompiler.h"
#endif

FString UEmeraldAuthoringLibrary::CompileMaterial(UMaterial* Material)
{
#if WITH_EDITOR
    if(!Material)return TEXT("Missing material");
    if(!FApp::CanEverRender())return TEXT("Material authoring requires AllowCommandletRendering with a real RHI");
    Material->UpdateCachedExpressionData();
    Material->ForceRecompileForRendering();
    FAssetCompilingManager::Get().FinishAllCompilation();
    if(GShaderCompilingManager)GShaderCompilingManager->FinishAllCompilation();
    FlushRenderingCommands();
    Material->MarkPackageDirty();
    const auto* Resource=Material->GetMaterialResource(GMaxRHIShaderPlatform);
    if(!Resource)return TEXT("No compiled resource for active shader platform");
    return FString::Join(Resource->GetCompileErrors(),TEXT("\n"));
#else
    return TEXT("Authoring requires an editor target");
#endif
}
