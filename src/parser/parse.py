import aiohttp
import asyncio
import itertools
import json


def process_pull_data(json_data):
    return {
        'title': json_data['title'],
        'diff': json_data['diff_url'],
        'body': json_data['body']
    }

async def get_repo_pulls(session, token, repo_owner, repo_name, only_closed=True, page=1):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        'state': 'closed' if only_closed else 'all',
        'per_page': 100,
        'page': page
    }
    async with session.get(url, headers=headers, params=params) as response:
        text = await response.text()
    return list(map(process_pull_data, json.loads(text)))

async def get_diff_data(session, token, pull_data):
    pull_data = pull_data.copy()
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(pull_data['diff'], headers=headers) as response:
        text = await response.text()
    pull_data['diff'] = text
    return pull_data


async def main():
    # REPO_OWNER + REPO_NAME
    with open('repos.json', 'rt') as jsonfile:
        repos_list = json.load(jsonfile)
    with open('tokens.json', 'rt') as jsonfile:
        list_of_tokens = json.load(jsonfile)

    tokens_iter = itertools.cycle(list_of_tokens)

    session = aiohttp.ClientSession()
    for owner, repo in repos_list:
        repo_result = []
        while True:
            curr_page = 1
            cleaned_data = await get_repo_pulls(session, next(tokens_iter), *repos_list[0], page=curr_page)
            if not cleaned_data:
                break
            else:
                cleaned_data_coros = [get_diff_data(session, token, data) for data, token in zip(cleaned_data, tokens_iter)]
                cleaned_data_coros = [get_diff_data(session, token, data) for data, token in zip(cleaned_data, tokens_iter)]
                repo_result.append(await asyncio.gather(*cleaned_data_coros))
                curr_page += 1
        with open(f'{owner}___{repo}.json', 'wt') as jsonfile:
            json.dump(repo_result, jsonfile)

    await session.close()

if __name__ is '__main__':
    asyncio.run(main)