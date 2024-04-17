import json

import requests


def parse_markdown_table():
    markdown = requests.get(
        "https://raw.githubusercontent.com/EvanLi/Github-Ranking/27472822252b7445c8bd74f24dbc6c48fa043bf6/Top100/Python.md"
    ).text

    table = []
    i = 0
    for line in markdown.split("\n"):
        if line.startswith("|"):
            i += 1
            if i <= 2:
                # skip header and delimiter
                continue
            # Ranking | Project Name | Stars | Forks | Language | Open Issues | Description | Last Commit
            name = line.split("|")[2]
            repo_name, url = name.split("](")
            url = url.rstrip(") ")
            repo_name = repo_name.lstrip(" [")
            stars = int(line.split("|")[3].strip())
            table.append({"repo_name": repo_name, "url": url, "stars": stars})
    return table


if __name__ == "__main__":
    res = parse_markdown_table()
    print(res)
    with open("repos.json", "w") as jsonfile:
        json.dump(res, jsonfile)
