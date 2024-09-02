import pandas as pd
import os
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

FIXED_Y_AXIS_LIMIT = 0.4
ASPECT_RATIO = (12, 8)


def estimate(
    axes,
    actual,
    expected,
    point_index,
    title,
    fixed_y_axis=False,
    include_2022_fit=False,
    include_2023_fit=False,
):
    actual["time"] = (
        pd.to_datetime(actual["date"], unit="ms") - pd.to_datetime("2016-01-01")
    ).dt.total_seconds() / (365.25 * 24 * 60 * 60)

    phi = 6.283 * actual["time"]
    phi_cos = phi.apply(math.cos)
    phi_sin = phi.apply(math.sin)

    actual["observation_estimate"] = (
        expected["intercept"] + expected["cos"] * phi_cos + expected["sin"] * phi_sin
    )

    actual["date"] = pd.to_datetime(actual["date"], unit="ms")

    filtered_data = actual[(actual["z"] != 0) & (actual["point"] == point_index)]

    if include_2022_fit:
        filtered_data_2022 = filtered_data[filtered_data["date"].dt.year == 2022]
        intercept = filtered_data_2022["INTP"].iloc[-1]
        cos0 = filtered_data_2022["COS0"].iloc[-1]
        sin0 = filtered_data_2022["SIN0"].iloc[-1]

        x = filtered_data["time"]

        A = np.sqrt(cos0**2 + sin0**2)
        phi = np.arctan2(sin0, cos0)

        y = intercept + A * np.cos(2 * np.pi * x - phi)

        axes.plot(filtered_data["date"], y, label="Final 2022 fit", color="orange")

    if include_2023_fit:
        filtered_data_2023 = filtered_data[filtered_data["date"].dt.year == 2023]
        intercept = filtered_data_2023["INTP"].iloc[-1]
        cos0 = filtered_data_2023["COS0"].iloc[-1]
        sin0 = filtered_data_2023["SIN0"].iloc[-1]

        x = filtered_data["time"]

        A = np.sqrt(cos0**2 + sin0**2)
        phi = np.arctan2(sin0, cos0)

        y = intercept + A * np.cos(2 * np.pi * x - phi)

        axes.plot(filtered_data["date"], y, label="Final 2023 fit", color="purple")

    axes.plot(
        filtered_data["date"],
        filtered_data["estimate"],
        label="Estimate - Optimized",
        linestyle="-",
        color="blue",
    )
    axes.plot(
        filtered_data["date"],
        filtered_data["observation_estimate"],
        label="Target",
        linestyle="--",
        color="green",
    )
    axes.scatter(
        filtered_data["date"], filtered_data["z"], label="Observed", s=13, color="red"
    )

    axes.xaxis.set_major_locator(mdates.AutoDateLocator())
    axes.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes.tick_params(axis='x', labelsize=8)

    max_estimate = max(filtered_data["estimate"])
    min_estimate = min(filtered_data["estimate"])

    # if max_estimate < 0.23:
    #     axes.set_ylim(min_estimate - 0.1, 0.25)

    if fixed_y_axis:
        axes.set_ylim(0, FIXED_Y_AXIS_LIMIT)

    axes.set_title(title)


def intercept_cos_sin(axes, actual, expected, point_index, title, fixed_y_axis=False):
    actual["target_intercept"] = expected["intercept"]
    actual["target_cos"] = expected["cos"]
    actual["target_sin"] = expected["sin"]

    actual["date"] = pd.to_datetime(actual["date"], unit="ms")

    filtered_data = actual[(actual["z"] != 0) & (actual["point"] == point_index)]

    dates = filtered_data["date"]
    intp = filtered_data["INTP"]
    cos = filtered_data["COS0"]
    sin = filtered_data["SIN0"]
    target_intercept = filtered_data["target_intercept"]
    target_cos = filtered_data["target_cos"]
    target_sin = filtered_data["target_sin"]

    axes.plot(dates, intp, label="intercept", linestyle="-", color="blue")
    axes.plot(
        dates, target_intercept, label="target intercept", linestyle="--", color="blue"
    )

    axes.plot(dates, cos, label="cos", linestyle="-", color="green")
    axes.plot(dates, target_cos, label="target cos", linestyle="--", color="green")

    axes.plot(dates, sin, label="sin", linestyle="-", color="red")
    axes.plot(dates, target_sin, label="target sin", linestyle="--", color="red")

    axes.xaxis.set_major_locator(mdates.AutoDateLocator())
    axes.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes.tick_params(axis='x', labelsize=8)

    if fixed_y_axis:
        axes.set_ylim(0, FIXED_Y_AXIS_LIMIT)

    axes.set_title(title)


def residuals_over_time(axes, actual, expected, point_index, title, fixed_y_axis=False):
    actual["intercept_residual"] = actual["INTP"] - expected["intercept"]
    actual["cos_residual"] = actual["COS0"] - expected["cos"]
    actual["sin_residual"] = actual["SIN0"] - expected["sin"]

    actual["date"] = pd.to_datetime(actual["date"], unit="ms")

    filtered_data = actual[(actual["z"] != 0) & (actual["point"] == point_index)]

    intercept_residual = filtered_data["intercept_residual"]
    cos_residual = filtered_data["cos_residual"]
    sin_residual = filtered_data["sin_residual"]
    dates = filtered_data["date"]

    axes.scatter(
        dates, intercept_residual, label="intercept", linestyle="-", color="blue", s=10
    )
    axes.scatter(dates, cos_residual, label="cos", linestyle="-", color="green", s=10)
    axes.scatter(dates, sin_residual, label="sin", linestyle="-", color="red", s=13)

    axes.axhline(y=0, color="black", linestyle="--")

    axes.xaxis.set_major_locator(mdates.AutoDateLocator())
    axes.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes.tick_params(axis='x', labelsize=8)

    axes.set_title(title)


def amplitude(axes, actual, expected, point_index, title, fixed_y_axis=False):
    actual["date"] = pd.to_datetime(actual["date"], unit="ms")
    actual["expected_cos"] = expected["cos"]
    actual["expected_sin"] = expected["sin"]
    actual["expected_amplitude"] = np.sqrt(expected["cos"] ** 2 + expected["sin"] ** 2)

    filtered_data = actual[(actual["z"] != 0) & (actual["point"] == point_index)]

    cos = filtered_data["COS0"]
    sin = filtered_data["SIN0"]
    dates = filtered_data["date"]

    amplitude_values = np.sqrt(cos**2 + sin**2)
    expected_amplitude = filtered_data["expected_amplitude"]

    axes.plot(
        dates,
        amplitude_values,
        label="Measured Amplitude",
        linestyle="-",
        color="purple",
    )
    axes.plot(
        dates,
        expected_amplitude,
        label="Expected Amplitude",
        linestyle="--",
        color="orange",
    )

    axes.xaxis.set_major_locator(mdates.AutoDateLocator())
    axes.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    axes.tick_params(axis='x', labelsize=8)

    axes.set_title(title)


def get_labels_and_handles(axs):
    handles, labels = axs.get_legend_handles_labels()
    unique_labels = []
    unique_handles = []

    for handle, label in zip(handles, labels):
        if label not in unique_labels:
            unique_handles.append(handle)
            unique_labels.append(label)

    return unique_labels, unique_handles


def save_chart(fig, point_index, name, output_directory):
    point_directory = f"{output_directory}/points/{point_index}"
    os.makedirs(point_directory, exist_ok=True)
    fig.savefig(f"{point_directory}/{name}.png")

    directory = f"{output_directory}/{name}"
    os.makedirs(directory, exist_ok=True)
    fig.savefig(f"{directory}/{point_index}.png")


def generate_charts_comparing_runs(
    data_files, observation_file_path, output_directory, flags
):
    os.makedirs(output_directory, exist_ok=True)
    target_observations = pd.read_csv(observation_file_path)
    points_count = len(target_observations["point"].unique())

    for point_index in range(points_count):

        plots = []

        if flags["estimate"]:
            fig_estimate_vs_target, axs_estimate_vs_target = plt.subplots(
                2, 2, figsize=(12, 8)
            )
            plots.append(
                (fig_estimate_vs_target, axs_estimate_vs_target, "estimate vs target")
            )
        if flags["intercept_cos_sin"]:
            fig_intercept_cos_sin, axs_intercept_cos_sin = plt.subplots(
                2, 2, figsize=(12, 8)
            )
            plots.append(
                (fig_intercept_cos_sin, axs_intercept_cos_sin, "intercept cos sin")
            )
        if flags["residuals"]:
            fig_residuals, axs_residuals = plt.subplots(2, 2, figsize=(12, 8))
            plots.append((fig_residuals, axs_residuals, "residuals over time"))
        if flags["amplitude"]:
            fig_amplitude, axs_amplitude = plt.subplots(2, 2, figsize=(12, 8))
            plots.append((fig_amplitude, axs_amplitude, "amplitude"))

        for file_index, run_title in enumerate(data_files.keys()):
            eeek_output = pd.read_csv(data_files[run_title])

            for fig, axs, graph_type in plots:
                axes = axs[file_index // 2, file_index % 2]
                if graph_type == "estimate vs target":
                    estimate(
                        axes,
                        eeek_output.copy(),
                        target_observations.copy(),
                        point_index,
                        run_title,
                        include_2022_fit=flags["final_2022_fit"],
                        include_2023_fit=flags["final_2023_fit"],
                    )
                elif graph_type == "intercept cos sin":
                    intercept_cos_sin(
                        axes,
                        eeek_output.copy(),
                        target_observations.copy(),
                        point_index,
                        run_title,
                    )
                elif graph_type == "residuals over time":
                    residuals_over_time(
                        axes,
                        eeek_output.copy(),
                        target_observations.copy(),
                        point_index,
                        run_title,
                    )
                elif graph_type == "amplitude":
                    amplitude(
                        axes,
                        eeek_output.copy(),
                        target_observations.copy(),
                        point_index,
                        run_title,
                    )

        for fig, axs, graph_type in plots:
            labels, handles = get_labels_and_handles(axs[0, 0])
            fig.legend(handles, labels, loc="upper center", ncol=5)

            plt.tight_layout()
            save_chart(fig, point_index, graph_type, output_directory)
            plt.close(fig)
