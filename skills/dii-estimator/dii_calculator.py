"""DII (Dietary Inflammatory Index) Calculator.

Calculates the Dietary Inflammatory Index score based on nutrient intake
compared to global reference values. Uses only Python standard library.
"""

import json
import math
import os
import sys


def norm_cdf(x):
    """Standard normal cumulative distribution function using math.erf."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def calculate_dii(nutrients, dii_params):
    """Calculate DII score from nutrients and parameter definitions.

    Args:
        nutrients: dict of nutrient_name -> value
        dii_params: dict of nutrient_name -> {inflammatory_score, global_mean, sd}

    Returns:
        (total_score, components_dict) where total_score is rounded to 4 decimals
        and components_dict maps nutrient_name to {score, percentile, z, direction, value}
    """
    components = {}
    total = 0.0

    for name, value in nutrients.items():
        if value is None:
            continue
        if name not in dii_params:
            continue

        param = dii_params[name]
        global_mean = param["global_mean"]
        sd = param["sd"]
        inflammatory_score = param["inflammatory_score"]

        z = (value - global_mean) / sd
        percentile = norm_cdf(z) * 2 - 1
        score = percentile * inflammatory_score

        if score < 0:
            direction = "anti"
        elif score == 0:
            direction = "neutral"
        else:
            direction = "pro"

        total += score
        components[name] = {
            "score": score,
            "percentile": percentile,
            "z": z,
            "direction": direction,
            "value": value,
        }

    return (round(total, 4), components)


def interpret_dii(dii_score):
    """Interpret a DII score into a level and label.

    Returns:
        (level, label) tuple
    """
    if dii_score < -1:
        return ("anti_inflammatory", "抗炎饮食")
    elif dii_score < 0:
        return ("mild_anti_inflammatory", "轻度抗炎饮食")
    elif dii_score < 1:
        return ("mild_pro_inflammatory", "轻度促炎饮食")
    else:
        return ("pro_inflammatory", "促炎饮食")


def main():
    """CLI entry point for DII calculation."""
    home = os.path.expanduser("~")
    default_input = os.path.join(home, ".longerian", "data", "dii", "dii_input.json")
    default_output = os.path.join(home, ".longerian", "data", "dii", "dii_result.json")
    default_params = os.path.join(home, ".longerian", "data", "dii", "dii_params.json")

    args = sys.argv[1:]
    input_path = args[0] if len(args) > 0 else default_input
    output_path = args[1] if len(args) > 1 else default_output

    # Load params
    with open(default_params, "r") as f:
        dii_params = json.load(f)

    # Load input
    with open(input_path, "r") as f:
        input_data = json.load(f)

    nutrients = input_data.get("nutrients", {})

    # Validate
    if not isinstance(nutrients, dict):
        print("Error: 'nutrients' must be a dictionary", file=sys.stderr)
        sys.exit(1)

    # Calculate
    dii_score, components = calculate_dii(nutrients, dii_params)
    level, label = interpret_dii(dii_score)
    parameters_used = len(components)
    total_parameters = len(dii_params)

    # Warn if low coverage
    if parameters_used < 10:
        print(f"Warning: only {parameters_used} nutrient components used (recommended >= 10)", file=sys.stderr)

    # Build result
    result = {
        "dii_score": dii_score,
        "interpretation": label,
        "level": level,
        "component_scores": {name: comp["score"] for name, comp in components.items()},
        "parameters_used": parameters_used,
        "total_parameters": total_parameters,
        "foods": input_data.get("foods", []),
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Print to stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
