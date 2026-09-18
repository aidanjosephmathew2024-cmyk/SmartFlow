import os
import shutil
import yaml

# ---- CONFIG ----
AMBULANCE_DIR = "datasets/roboflow-ambulance"
VEHICLE_DIR = "datasets/roboflow-vehicles"
MERGED_DIR = "datasets/merged-dataset"

UNIFIED_CLASSES = ["car", "bike", "bus", "truck", "ambulance"]

# Keywords to auto-match each source dataset's class names to our unified list
KEYWORD_MAP = {
    "car": ["car"],
    "bike": ["bike", "motorcycle", "two-wheeler", "bicycle", "cycle"],
    "bus": ["bus"],
    "truck": ["truck", "trucks", "lorry", "van"],
    "ambulance": ["ambulance"],
}


def load_yaml_classes(dataset_dir):
    with open(os.path.join(dataset_dir, "data.yaml"), "r") as f:
        data = yaml.safe_load(f)
    return data["names"]


def build_class_index_map(source_names):
    """Map each source class index -> unified class index, or None if unused."""
    mapping = {}
    for idx, name in enumerate(source_names):
        name_lower = str(name).lower()
        matched = None
        for unified_class, keywords in KEYWORD_MAP.items():
            if any(kw in name_lower for kw in keywords):
                matched = unified_class
                break
        if matched:
            mapping[idx] = UNIFIED_CLASSES.index(matched)
        else:
            mapping[idx] = None  # class not used in unified set (e.g. "person", "tractor123")
    return mapping


def process_split(source_dir, split, class_index_map, merged_dir, prefix):
    """Copy images + remap labels for one split (train/valid) from one source dataset."""
    src_images = os.path.join(source_dir, split, "images")
    src_labels = os.path.join(source_dir, split, "labels")

    dst_images = os.path.join(merged_dir, split, "images")
    dst_labels = os.path.join(merged_dir, split, "labels")
    os.makedirs(dst_images, exist_ok=True)
    os.makedirs(dst_labels, exist_ok=True)

    if not os.path.isdir(src_labels):
        print(f"  Skipping {split} — no labels folder found at {src_labels}")
        return 0

    count = 0
    for label_file in sorted(os.listdir(src_labels)):
        if not label_file.endswith(".txt"):
            continue

        src_label_path = os.path.join(src_labels, label_file)
        with open(src_label_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            old_class_id = int(parts[0])
            new_class_id = class_index_map.get(old_class_id)
            if new_class_id is None:
                continue
            parts[0] = str(new_class_id)
            new_lines.append(" ".join(parts))

        if not new_lines:
            continue

        # Short, safe filename — avoids Windows path length limits
        count += 1
        new_base_name = f"{prefix}_{count:05d}"

        with open(os.path.join(dst_labels, f"{new_base_name}.txt"), "w") as f:
            f.write("\n".join(new_lines) + "\n")

        base_name = os.path.splitext(label_file)[0]
        for ext in [".jpg", ".jpeg", ".png"]:
            src_img = os.path.join(src_images, base_name + ext)
            if os.path.exists(src_img):
                dst_img = os.path.join(dst_images, f"{new_base_name}{ext}")
                shutil.copy2(src_img, dst_img)
                break

    print(f"  {split}: processed {count} labeled images from {source_dir}")
    return count


def main():
    print("Loading class lists...")
    ambulance_classes = load_yaml_classes(AMBULANCE_DIR)
    vehicle_classes = load_yaml_classes(VEHICLE_DIR)

    print(f"Ambulance dataset classes: {ambulance_classes}")
    print(f"Vehicle dataset classes: {vehicle_classes}")

    ambulance_map = build_class_index_map(ambulance_classes)
    vehicle_map = build_class_index_map(vehicle_classes)

    print(f"Ambulance class mapping: {ambulance_map}")
    print(f"Vehicle class mapping: {vehicle_map}")

    for split in ["train", "valid"]:
        print(f"\nProcessing split: {split}")
        process_split(AMBULANCE_DIR, split, ambulance_map, MERGED_DIR, prefix="amb")
        process_split(VEHICLE_DIR, split, vehicle_map, MERGED_DIR, prefix="veh")

    # Write unified data.yaml
    yaml_content = {
        "train": "train/images",
        "val": "valid/images",
        "nc": len(UNIFIED_CLASSES),
        "names": UNIFIED_CLASSES,
    }
    with open(os.path.join(MERGED_DIR, "data.yaml"), "w") as f:
        yaml.dump(yaml_content, f, default_flow_style=False)

    print(f"\n✅ Merge complete. Unified dataset created at: {MERGED_DIR}")
    print(f"Classes: {UNIFIED_CLASSES}")


if __name__ == "__main__":
    main()