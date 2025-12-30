import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import json
import matplotlib as mpl
from matplotlib.lines import Line2D
from matplotlib.offsetbox import OffsetImage, AnnotationBbox  # ← ONLY ADDITION


def render_map(
    data_csv_path="config/data.csv",
    title_text=None,
    source_text=None,
    credits_text=None,
    value_prefix="",
    value_suffix="",
    palette="Blues",
    annotation_text="",
    output_path="output/india_heatmap.png"
):

    # =============================
    # GLOBAL FONT (ROBOTO)
    # =============================
    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = ["Roboto", "DejaVu Sans", "Arial"]

    # =============================
    # HELPER FUNCTIONS
    # =============================
    def wrap_text_by_words(text, words_per_line=5):
        words = text.split()
        lines = [
            " ".join(words[i:i + words_per_line])
            for i in range(0, len(words), words_per_line)
        ]
        return "\n".join(lines)

    def get_text_color(value, cmap, norm):
        if value is None or value == "NA":
            return "black"

        r, g, b, _ = cmap(norm(value))
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return "white" if luminance < 0.55 else "black"

    def get_neighbor_based_color(neighbor_state, india_gdf, cmap, norm):
        row = india_gdf.loc[india_gdf["canonical_state"] == neighbor_state]
        if row.empty or pd.isna(row.iloc[0]["value"]):
            return "black"
        return get_text_color(row.iloc[0]["value"], cmap, norm)

    # =============================
    # USER CONFIG
    # =============================
    TITLE_TEXT = title_text if title_text else ""
    SOURCE_TEXT = source_text if source_text else ""
    CREDITS_TEXT = credits_text if credits_text else ""
    VALUE_PREFIX = value_prefix
    VALUE_SUFFIX = value_suffix

    WRAP_TITLE = True
    TITLE_WORDS_PER_LINE = 5
    ANNOTATION_TEXT = annotation_text if annotation_text else ""

    SMALL_LABEL_STATES = {
        "Delhi", "Punjab", "HR", "Uttarakhand",
        "Himachal", "Assam", "Meghalaya", "Jharkhand"
    }

    KERALA_LIKE_BLACK_STATES = {
        "Kerala",
        "Sikkim",
        "Arunachal",
        "Mizoram",
        "Tripura",
        "Andaman & Nicobar Islands",
        "Dadra & Nagar Haveli and Daman & Diu",
        "Goa",
        "Manipur",
        "Nagaland",
        "Lakshadweep",
        "Puducherry",
        "Chandigarh"
    }

    VALUE_BOLD_STATES = {
        "Maharashtra",
        "Rajasthan",
        "Gujarat",
        "Uttar Pradesh",
        "Karnataka",
        "Andhra Pradesh",
        "Tamil Nadu",
        "Madhya Pradesh",
        "Ladakh"
    }

    # =============================
    # LOAD FILES
    # =============================
    india = gpd.read_file("geo/india_states.geojson")
    labels = pd.read_csv("config/label_positions.csv")
    data = pd.read_csv(data_csv_path)

    with open("config/state_aliases.json", "r") as f:
        aliases = json.load(f)

    data["canonical_state"] = data["state"].apply(lambda x: aliases.get(x, x))
    india["canonical_state"] = india["name"].apply(lambda x: aliases.get(x, x))

    india = india.merge(
        data[["canonical_state", "value"]],
        on="canonical_state",
        how="left"
    )

    # =============================
    # FIGURE
    # =============================
    fig, ax = plt.subplots(figsize=(8, 10), facecolor="#F2EFEB")
    ax.set_facecolor("#F2EFEB")

    plt.subplots_adjust(left=0.02, right=0.98, top=0.89, bottom=0.045)

    cmap = mpl.cm.get_cmap(palette)
    norm = mpl.colors.Normalize(
        vmin=data["value"].min(),
        vmax=data["value"].max()
    )

    india.plot(
        column="value",
        ax=ax,
        cmap=cmap,
        linewidth=0.8,
        edgecolor="black",
        legend=False,
        missing_kwds={"color": "#eeeeee"}
    )

    ax.axis("off")

    # =============================
    # IDENTITY LINE
    # =============================
    fig.add_artist(Line2D(
        [0.42, 0.58],
        [0.988, 0.988],
        transform=fig.transFigure,
        color="#c0245d",
        linewidth=7
    ))

    # =============================
    # TITLE
    # =============================
    final_title = wrap_text_by_words(TITLE_TEXT, TITLE_WORDS_PER_LINE)
    fig.text(
        0.5, 0.955, final_title,
        ha="center", va="top",
        fontsize=22, weight="bold",
        linespacing=1.6
    )

    # =============================
    # LEGEND
    # =============================
    cax = fig.add_axes([0.55, 0.78, 0.30, 0.018])
    cbar = mpl.colorbar.ColorbarBase(
        cax, cmap=cmap, norm=norm, orientation="horizontal"
    )
    cbar.set_label(
        "DataVizPulse / Vijay",
        fontsize=9,
        fontweight="bold",
        labelpad=6
    )
    cbar.ax.xaxis.set_label_position("top")
    cbar.ax.xaxis.set_ticks_position("bottom")

    # =============================
    # LABELS
    # =============================
    for _, row in labels.iterrows():
        raw_state = row["state"]
        canonical_state = aliases.get(raw_state, raw_state)
        x, y = row["x"], row["y"]

        value_arr = india.loc[
            india["canonical_state"] == canonical_state, "value"
        ].values
        value = value_arr[0] if len(value_arr) and pd.notna(value_arr[0]) else "NA"

        display_value = (
            f"{VALUE_PREFIX}{value}{VALUE_SUFFIX}" if value != "NA" else "NA"
        )

        if raw_state in KERALA_LIKE_BLACK_STATES:
            text_color = "black"
        elif raw_state == "Delhi":
            text_color = get_neighbor_based_color(
                "Uttar Pradesh", india, cmap, norm
            )
        else:
            text_color = get_text_color(value, cmap, norm)

        value_color = (
            "black"
            if raw_state in KERALA_LIKE_BLACK_STATES or raw_state == "Meghalaya"
            else text_color
        )

        name_fontsize = 5.2 if raw_state in SMALL_LABEL_STATES else 7
        value_fontsize = 7.2 if raw_state in SMALL_LABEL_STATES else 9
        value_weight = "bold" if raw_state in VALUE_BOLD_STATES else "normal"

        if raw_state == "Assam":
            ax.text(
                x, y,
                f"{raw_state} {display_value}",
                fontsize=value_fontsize,
                ha="center", va="center",
                color=text_color,
                fontweight=value_weight,
                zorder=10,
                clip_on=False
            )
        else:
            ax.text(
                x, y + 0.08,
                raw_state,
                fontsize=name_fontsize,
                ha="center", va="bottom",
                color=text_color,
                zorder=10,
                clip_on=False
            )

            ax.text(
                x, y - 0.08,
                display_value,
                fontsize=value_fontsize,
                ha="center", va="top",
                color=value_color,
                fontweight=value_weight,
                zorder=10,
                clip_on=False
            )

    # =============================
    # ANNOTATION
    # =============================
    if ANNOTATION_TEXT:
        fig.text(
            0.785, 0.365,
            wrap_text_by_words(ANNOTATION_TEXT, 5),
            ha="center", va="center",
            fontsize=10, fontweight="bold",
            color="black", linespacing=1.5
        )

    # =============================
    # SOURCE
    # =============================
    fig.text(
        0.04, 0.035, SOURCE_TEXT,
        ha="left", va="bottom",
        fontsize=11, fontweight="bold",
        color="black"
    )

    # =============================
    # LOGO (BOTTOM RIGHT)
    # =============================
    try:
        logo = plt.imread("map_assets/logo.png")
        imagebox = OffsetImage(logo, zoom=0.033)
        ab = AnnotationBbox(
            imagebox,
            (0.965, 0.022),
            xycoords="figure fraction",
            frameon=False,
            box_alignment=(1, 0)
        )
        fig.add_artist(ab)
    except Exception as e:
        print("Logo not found:", e)

    # =============================
    # SAVE
    # =============================
    plt.savefig(output_path, dpi=500, facecolor=fig.get_facecolor())
    plt.close()

    print("India heatmap created successfully")








