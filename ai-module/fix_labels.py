import os

def fix_labels(folder):
    count = 0
    for filename in os.listdir(folder):
        if not filename.endswith('.txt'):
            continue
        path = os.path.join(folder, filename)
        with open(path, 'r') as f:
            lines = f.readlines()

        new_lines = []
        changed = False
        for line in lines:
            parts = line.strip().split(' ')
            if parts and parts[0] == '1':
                parts[0] = '0'
                changed = True
            new_lines.append(' '.join(parts))

        if changed:
            count += 1
            with open(path, 'w') as f:
                f.write('\n'.join(new_lines) + '\n')

    print(f"Fixed {count} files in {folder}")

fix_labels('datasets/roboflow-ambulance/train/labels')
fix_labels('datasets/roboflow-ambulance/valid/labels')
fix_labels('datasets/roboflow-ambulance/test/labels')