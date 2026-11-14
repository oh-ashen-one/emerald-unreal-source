#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EmeraldFoliageCluster.generated.h"
class UHierarchicalInstancedStaticMeshComponent;

// Serialized renderer data only; all placement is generated from the source plan.
UCLASS()
class EMERALD_API AEmeraldFoliageCluster : public AActor
{
    GENERATED_BODY()
public:
    AEmeraldFoliageCluster();
    UFUNCTION(BlueprintCallable,Category="Emerald|Authoring")
    void FinalizeInstances();
    virtual void BeginPlay() override;
private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Foliage;
};
