"""Git branch to Databricks environment. One direction, three doors.

Code moves feature/* → develop → ppe → main. Each merge is a pull request.
main is the prod git branch. There is no git branch named prod or dev.
The Databricks target for main is prod.
"""

from __future__ import annotations

from dataclasses import dataclass

# Same strings as databricks/variables.yml. Tests fail if the two copies drift.
CATALOG = "dbw_iris_ml_dev"
MODEL_NAME = "iris_species"
ENDPOINT_PREFIX = "iris-species"
TRAIN_JOB_PREFIX = "iris-ml-train"
INFER_JOB_PREFIX = "iris-ml-infer"
PROJECT = "iris-ml"
WORKSPACE_HOST = "https://adb-7405619226406985.5.azuredatabricks.net"
SERVERLESS_CLIENT = "4"


def registered_model_name(env_suffix: str) -> str:
    """Unity Catalog name catalog.schema.model for one environment."""
    return f"{CATALOG}.{env_suffix}.{MODEL_NAME}"


def serving_endpoint_name(env_suffix: str) -> str:
    """Serving endpoint and experiment name for one environment."""
    return f"{ENDPOINT_PREFIX}-{env_suffix}"


@dataclass(frozen=True, slots=True)
class PromotionStage:
    """One door: the git branch that may deploy one Databricks target."""

    order: int
    git_branch: str
    databricks_target: str
    endpoint_name: str
    model_name: str
    model_alias: str
    azure_environment: str
    variable_group: str


PROMOTION: tuple[PromotionStage, ...] = (
    PromotionStage(
        order=1,
        git_branch="develop",
        databricks_target="develop",
        endpoint_name=serving_endpoint_name("develop"),
        model_name=registered_model_name("develop"),
        model_alias="develop",
        azure_environment="iris-develop",
        variable_group="iris-develop",
    ),
    PromotionStage(
        order=2,
        git_branch="ppe",
        databricks_target="ppe",
        endpoint_name=serving_endpoint_name("ppe"),
        model_name=registered_model_name("ppe"),
        model_alias="ppe",
        azure_environment="iris-ppe",
        variable_group="iris-ppe",
    ),
    PromotionStage(
        order=3,
        git_branch="main",
        databricks_target="prod",
        endpoint_name=serving_endpoint_name("prod"),
        model_name=registered_model_name("prod"),
        model_alias="prod",
        azure_environment="iris-prod",
        variable_group="iris-prod",
    ),
)


def stage_for_target(target: str) -> PromotionStage:
    """Return the stage whose Databricks target is `target`."""
    for stage in PROMOTION:
        if stage.databricks_target == target:
            return stage
    known = ", ".join(stage.databricks_target for stage in PROMOTION)
    raise KeyError(f"unknown Databricks target {target!r}; expected one of {known}")


def stage_for_branch(branch: str) -> PromotionStage:
    """Return the stage deployed from this git branch name."""
    name = normalize_branch(branch)
    for stage in PROMOTION:
        if stage.git_branch == name:
            return stage
    known = ", ".join(stage.git_branch for stage in PROMOTION)
    raise KeyError(f"git branch {name!r} does not deploy; expected one of {known}")


def normalize_branch(ref: str) -> str:
    """Turn refs/heads/main or main into main."""
    name = ref.strip()
    prefix = "refs/heads/"
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name
