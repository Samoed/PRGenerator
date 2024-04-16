import asyncio
import itertools
import json
import os.path
from asyncio import sleep

import aiohttp
import requests
from aiohttp import ClientSession
from tqdm import tqdm

DATA_DIR = "data"


def bearer_token(token: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + token}


def process_pull_data(json_data):
    return {
        "title": json_data["title"],
        "diff": json_data["diff_url"],
        "body": json_data["body"],
        "url": json_data["url"],
        "created_at": json_data["created_at"],
        "closed_at": json_data["closed_at"],
        "merged_at": json_data["merged_at"],
        "updated_at": json_data["updated_at"],
    }


def get_repo_pulls(token: str, repo_owner: str, repo_name: str, only_closed: bool = True, page: int = 1) -> list[dict]:
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    params = {"state": "closed" if only_closed else "all", "per_page": 100, "page": page}
    text = requests.get(url, headers=bearer_token(token), params=params).text
    return list(map(process_pull_data, json.loads(text)))


async def get_diff_data(session: ClientSession, token: str, pull_data: dict[str, str]) -> dict[str, str]:
    pull_data = pull_data.copy()
    async with session.get(pull_data["diff"], headers=bearer_token(token)) as response:
        text = await response.text()
    pull_data["diff"] = text
    return pull_data


def get_count_of_pulls(token: str, repo_owner: str, repo_name: str) -> int:
    url = f"https://api.github.com/search/issues?q=type:pr state:closed is:pull-request repo:{repo_owner}/{repo_name}"
    text = requests.get(url, headers=bearer_token(token)).json()
    return text["total_count"]


async def main():
    with open("repos_selected.json") as jsonfile:
        repos_list = json.load(jsonfile)
    with open("tokens_private.json") as jsonfile:
        list_of_tokens = json.load(jsonfile)

    tokens_iter = itertools.cycle(list_of_tokens)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    for i, repo_data in enumerate(repos_list):
        url = repo_data["url"]
        repo_name = url.split("/")[-1]
        owner = url.split("/")[-2]
        count_of_pulls = get_count_of_pulls(next(tokens_iter), repo_owner=owner, repo_name=repo_name)
        for curr_page in tqdm(range(count_of_pulls // 100 + 1), desc=f"[{i}/{len(repos_list)}] {owner}/{repo_name}"):
            cleaned_data = get_repo_pulls(next(tokens_iter), repo_owner=owner, repo_name=repo_name, page=curr_page)
            if not cleaned_data:
                break
            async with aiohttp.ClientSession() as session:
                try:
                    cleaned_data_coros = [
                        get_diff_data(session, token, data)
                        for data, token in zip(cleaned_data, tokens_iter, strict=False)
                    ]
                except Exception as e:
                    print(e)
                    await sleep(10)
                repo_result = await asyncio.gather(*cleaned_data_coros)
            repo_dir = os.path.join(DATA_DIR, f"{owner}_{repo_name}")
            if not os.path.exists(repo_dir):
                os.makedirs(repo_dir)
            with open(os.path.join(repo_dir, str(curr_page) + ".json"), "w") as jsonfile:
                json.dump(repo_result, jsonfile)


if __name__ == "__main__":
    asyncio.run(main())
