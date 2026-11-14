#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "EmeraldAuthoringLibrary.generated.h"
class UMaterial;

// Editor pipeline only. Python calls native cache/shader compilation explicitly;
// no Blueprint gameplay or external bridge is introduced.
UCLASS()
class EMERALD_API UEmeraldAuthoringLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable,Category="Emerald|Authoring")
    static FString CompileMaterial(UMaterial* Material);
};
