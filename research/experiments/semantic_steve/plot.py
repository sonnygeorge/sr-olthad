import os
import random

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.image import imread


def create_paired_boxplots(
    vlm_data, human_data, pair_texts, image_paths, output_path="boxplot_comparison.png"
):
    """
    Create a figure with 3 pairs of boxplots comparing VLM and human data.

    Parameters:
    -----------
    vlm_data : list of lists
        A list containing 3 lists of VLM data points
    human_data : list of lists
        A list containing 3 lists of human data points
    pair_texts : list of str
        Labels for each pair of boxplots
    image_paths : list of str
        Paths to images for each pair
    output_path : str, optional
        Path to save the output figure
    """
    # Set figure size and create figure
    fig, ax = plt.subplots(figsize=(14, 3))

    # Set positions for boxplots - create positions with pairs closer together
    positions = []
    for i in range(3):
        positions.extend([i * 3, i * 3 + 0.8])  # Closer within pairs

    # Create boxplots
    vlm_positions = [positions[i] for i in range(len(positions)) if i % 2 == 0]
    human_positions = [positions[i] for i in range(len(positions)) if i % 2 == 1]

    vlm_boxes = ax.boxplot(
        [vlm_data[0], vlm_data[1], vlm_data[2]],
        positions=vlm_positions,
        patch_artist=True,
        widths=0.6,
    )

    human_boxes = ax.boxplot(
        [human_data[0], human_data[1], human_data[2]],
        positions=human_positions,
        patch_artist=True,
        widths=0.6,
    )

    # Color the boxplots
    for box in vlm_boxes["boxes"]:
        box.set(facecolor="blue", alpha=0.7)

    for box in human_boxes["boxes"]:
        box.set(facecolor="green", alpha=0.7)

    # Set y-axis range and labels
    ax.set_ylim(-0.1, 1.25)  # Slightly extended for visibility
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_yticklabels(
        [
            "disagree 0.0",
            "somewhat disagree 0.25",
            "neutral 0.5",
            "somewhat agree 0.75",
            "agree 1.0",
        ],
        fontsize=11.5,
    )

    # Calculate pair centers
    pair_centers = [
        (vlm_positions[i] + human_positions[i]) / 2 for i in range(len(vlm_positions))
    ]

    # Set x-ticks at pair centers with pair_texts as labels
    ax.set_xticks(pair_centers)
    ax.set_xticklabels(pair_texts, fontsize=12)

    # Add title at the TOP of the plot
    plt.title(
        "Statement: the image evidences that the player fulfilled the task, 'take a screenshot of _____'",
        fontsize=14,
        pad=10,
    )

    # Add legend
    vlm_patch = mpatches.Patch(color="blue", alpha=0.7, label="GPT-4.1")
    human_patch = mpatches.Patch(color="green", alpha=0.7, label="Human")
    ax.legend(handles=[vlm_patch, human_patch], loc="upper right", bbox_to_anchor=(1, 1))

    # Define the figure region for the plot
    ax.set_xlim(-1, max(positions) + 1)

    # Calculate the space needed for the images
    img_height_ratio = 0.48  # Proportion of figure height for images

    # First adjust the main plot to make room for images below
    plt.subplots_adjust(bottom=0.25)  # Increase bottom margin to make room for images

    # Apply tight layout to the main plot area
    plt.tight_layout()

    # Get tick positions AFTER layout adjustment
    fig.canvas.draw()

    # Get the transformed positions for the centers
    display_to_fig = fig.transFigure.inverted()

    # Transform the pair centers from data coordinates to figure coordinates
    img_positions = []
    for center in pair_centers:
        # Convert from data coordinates to display coordinates
        display_coords = ax.transData.transform((center, 0))
        # Convert from display coordinates to figure coordinates
        fig_coords = display_to_fig.transform(display_coords)
        img_positions.append(fig_coords[0])

    # Get the position of the bottom tick labels
    # We need to find the bottom position of the x-tick labels
    tick_boxes = [label.get_window_extent() for label in ax.get_xticklabels()]
    tick_bottoms = [box.transformed(display_to_fig).y0 for box in tick_boxes]
    lowest_tick_point = min(tick_bottoms) if tick_bottoms else 0.2  # Default if no ticks

    # Add images below the x-tick labels with proper spacing
    img_width = 0.2  # Width of each image in figure coordinates
    img_bottom_position = lowest_tick_point - 0.02  # Small gap between labels and images
    img_height = img_height_ratio  # Height of each image in figure coordinates

    # Add images
    for img_path, pos in zip(image_paths, img_positions, strict=False):
        # Add image
        img = imread(img_path)
        # Create an inset axis for the image
        img_box = fig.add_axes(
            [pos - img_width / 2, img_bottom_position - img_height, img_width, img_height]
        )  # [left, bottom, width, height]
        img_box.imshow(img)
        img_box.axis("off")

    # Save figure with adjusted bbox to include the images
    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    return fig


if __name__ == "__main__":
    # Generate random sample data from the possible values
    possible_values = [0, 0.25, 0.5, 0.75, 1]

    # Generate data for each distribution (5 points each)
    vlm_data = [
        [random.choice(possible_values) for _ in range(15)],
        [random.choice(possible_values) for _ in range(15)],
        [random.choice(possible_values) for _ in range(15)],
    ]

    human_data = [
        [random.choice(possible_values) for _ in range(15)],
        [random.choice(possible_values) for _ in range(15)],
        [random.choice(possible_values) for _ in range(15)],
    ]

    # Example pair texts and image paths (replace with actual paths)
    pair_texts = [
        "'a hole that you dug'",
        "'an animal whose enclosure gives it a reason to be happy'",
        "'two villagers'",
    ]
    images_dir = os.getcwd()  # Current working directory
    image_paths = [
        os.path.join(images_dir, "dug_hole.png"),
        os.path.join(images_dir, "pig_enclosure.png"),
        os.path.join(images_dir, "villager.png"),
    ]

    # Create the figure
    fig = create_paired_boxplots(vlm_data, human_data, pair_texts, image_paths)

    plt.show()
