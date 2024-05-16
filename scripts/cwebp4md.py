import os
from os import path, getcwd
import re
import sys
from glob import glob
from PIL import Image, ImageSequence
import multiprocessing


def find_md_files(pattern):
    return glob(pattern)


def find_md_files_in_directory(directory, recursive=False):
    if recursive:
        pattern = path.join(directory, "**", "*.md")
    else:
        pattern = path.join(directory, "*.md")
    return glob(pattern, recursive=recursive)


def find_local_images(md_content):

    # 使用正则表达式找到所有图片路径，并排除 http 和 .webp
    pattern = r"((?<!<!-- )!\[(.*?)\]\((?!http[s]?:)(?!.*\.webp\))(.*?)\))(?!.*-->)"
    all_images = re.findall(pattern, md_content)
    return all_images


def convert_image_to_webp(image_path, markdown_path, quality=80):

    if not path.isabs(image_path):
        # 获取图片的绝对路径
        abs_image_path = path.join(path.dirname(markdown_path), image_path)
    else:
        abs_image_path = image_path
    # 检查图片是否存在
    abs_image_path = path.normpath(abs_image_path)

    if not path.exists(abs_image_path):
        print(f"\n[{markdown_path}]\n  Warning: Image '{abs_image_path}' not found. Skipping...")
        return False

    # 获取文件路径、文件名和扩展名
    dirname = path.dirname(abs_image_path)
    basename = path.basename(abs_image_path)
    filename, ext = path.splitext(basename)
    output_path = path.join(dirname, f"{filename}.webp")
    output_path = path.normpath(output_path)

    # 判断webp是否已经存在
    if ext.lower() != ".webp" and not path.exists(output_path):
        if ext.lower() == ".gif":
            with Image.open(abs_image_path) as img:
                frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                frames[0].save(
                    output_path, format="WEBP", save_all=True, append_images=frames[1:], loop=0, duration=img.info["duration"], quality=quality, method=6
                )
        else:
            with Image.open(abs_image_path) as img:
                img.save(output_path, "WEBP", quality=quality, method=6)
        print(f"\n[{markdown_path}]\n  Convert '{abs_image_path}' ---> '{output_path}'")

    # 获取新的相对路径，并保留 ./ 前缀
    output_path = path.relpath(output_path, path.dirname(markdown_path))
    output_path = path.normpath(output_path)
    output_path = output_path.replace("\\", "/")
    if not output_path.startswith("./"):
        output_path = "./" + output_path
    return output_path


def process_markdown(markdown_path, option_replace):
    def replace_image(match):
        full_match, alt_text, image_path = match.groups()
        new_image_path = convert_image_to_webp(image_path, markdown_path)
        if new_image_path == False:
            return full_match
        if option_replace:
            return f"![{alt_text}]({new_image_path})"
        else:
            return f"<!-- {full_match} --> ![{alt_text}]({new_image_path})"

    # 定义一个函数，用于分割文本为多个段落，标记每个段落是文本还是代码
    def split_text(md_content):
        segments = re.split(r"(```.*?```)", md_content, flags=re.DOTALL)
        segmented_content = []
        for i, segment in enumerate(segments):
            if i % 2 == 0:
                # 文本段
                segmented_content.append(("text", segment))
            else:
                # 代码段
                segmented_content.append(("code", segment))
        return segmented_content

    with open(markdown_path, "r", encoding="utf-8") as file:
        md_content = file.read()

    # 分割文本为多个段落，标记每个段落是文本还是代码
    segmented_content = split_text(md_content)

    # print("===========================================================")
    # for i in range(len(segmented_content)):
    #     print(segmented_content[i])
    #     print("===========================================================")

    pattern = r"((?<!<!-- )!\[(.*?)\]\((?!http[s]?:)(?!.*\.webp\))(.*?)\))(?!.*-->)"
    # 对文本段中的图片引用进行替换
    for i, (segment_type, segment) in enumerate(segmented_content):
        if segment_type == "text":
            segmented_content[i] = (
                "text",
                re.sub(pattern, replace_image, segment),
            )

    # print("\n\n===========================================================")
    # for i in range(len(segmented_content)):
    #     print(segmented_content[i])
    #     print("===========================================================")
    # 重新拼接文本段和代码段
    processed_md_content = "".join(segment for _, segment in segmented_content)
    # print(f"\n{processed_md_content}")

    # 写回Markdown文件
    with open(markdown_path, "w", encoding="utf-8") as file:
        file.write(processed_md_content)


def process_markdown_file(markdown_path, option_replace):
    print(f"Processing '{markdown_path}'...")

    if not path.isfile(markdown_path):
        print(f"Warning: File '{markdown_path}' not found. Skipping...")
        return

    process_markdown(markdown_path, option_replace)


def print_help():
    help_message = """
    Usage: python cwebp4md.py <input_file_pattern> [-r <directory>] [-d <directory>] [--replace] [-h | --help]

    Options:
        <input_file_pattern>    Pattern to match markdown files (e.g., "*.md").
        -r <directory>          Specify directory to search for markdown files recursively.
        -d <directory>          Specify directory to search for markdown files non-recursively.
        --replace               Replace original image links with new ones directly in the markdown files.
                                By default, the script will comment out the original image links and add new ones.
        -h, --help              Show this help message and exit.

    Description:
        This script processes markdown files to update image links. By default, it comments out the original image 
        links and adds new image links in the markdown files. The --replace option allows the script to replace 
        the original image links directly.

    Example:
        python cwebp4md.py "*.md" -r ./docs -d ./notes
        python cwebp4md.py "*.md" --replace -r ./docs -d ./notes
    """
    print(help_message)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) < 2 or "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    input_patterns = []
    directories = []
    md_files = []
    recursive_search = False
    option_replace = False

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-r" and i + 1 < len(sys.argv):
            directories.append((sys.argv[i + 1], True))
            i += 1
        elif sys.argv[i] == "-d" and i + 1 < len(sys.argv):
            directories.append((sys.argv[i + 1], False))
            i += 1
        elif sys.argv[i] == "--replace":
            option_replace = True
        else:
            input_patterns.append(sys.argv[i])
        i += 1

    current_directory = os.getcwd()
    print("工作路径：", current_directory)

    for pattern in input_patterns:
        md_files.extend(find_md_files(pattern))

    for directory, recursive in directories:
        md_files.extend(find_md_files_in_directory(directory, recursive))

    if not md_files:
        print(f"Error: No files matched the pattern '{input_patterns}'")
        sys.exit(1)

    print("待处理 .md 文件数量：", len(md_files))
    for i in range(len(md_files)):
        if not path.isabs(md_files[i]):
            md_files[i] = path.join(current_directory, md_files[i])
        md_files[i] = path.normpath(md_files[i])
        print(f"{i+1}. {md_files[i]}")

    try:
        with multiprocessing.Pool() as pool:
            pool.starmap(process_markdown_file, [(markdown_path, option_replace) for markdown_path in md_files])
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, terminating workers")
        pool.terminate()
        pool.join()
    else:
        pool.close()
        pool.join()

    print("Markdown files updated successfully.")
