import os

def print_tree(startpath, max_depth=3, prefix="", output_file="tree_output.txt"):
    start_depth = startpath.count(os.sep)
    with open(output_file, "w", encoding="utf-8") as f:
        for root, dirs, files in os.walk(startpath):
            depth = root.count(os.sep) - start_depth
            if depth >= max_depth:
                continue
            f.write(prefix + "    " * depth + "|-- " + os.path.basename(root) + "/\n")
            for file in files:
                f.write(prefix + "    " * (depth + 1) + "|-- " + file + "\n")

print_tree(".", max_depth=3)
