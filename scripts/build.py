import functools
import json
import re
import semver
import subprocess as sp

def exec(*argv):
    res = sp.run(argv, capture_output=True)
    if not res.returncode == 0:
        print('Error running', argv)
        print('StdOut:\n', res.stdout)
        print('StdErr:\n', res.stderr)
        raise Exception('Failed to exec ' + " ".join(argv))
    return res


def runHugo(outSuffix=""):
    return exec(
        "hugo",
		"--destination=public/" + outSuffix,
		"--baseURL",
        "https://tour.dgraph.io/" + outSuffix,
        "--config",
        "config.toml,releases.json",
        )


def getReleases():
    gitBranches = exec("git", "branch")
    branches = gitBranches.stdout.decode('utf8')
    branches = branches.split('\n')
    res = []
    for b in branches:
        match = re.compile(r"[ *]+dgraph-([0-9.]+)").match(b)
        if match:
            res.append(match.group(1))
    print('Found release versions', res)

    res.sort(key=functools.cmp_to_key(semver.compare), reverse=True)

    res = ["master"] + res
    print('Order on the webpage: ', res)
    return res

def buildBranch(branch, dest, jsonData):
    print("Building", branch, "to public/" + dest)
    res = exec("git", "checkout", branch)

    with open('releases.json', 'w') as f:
        f.write(json.dumps(jsonData))

    runHugo(dest)

def buildAll(releases):
    latestRelease = releases[1]
    print('Latest Release (recommended to users): ', latestRelease)

    def jsonFor(version, latestRelease, releases):
        return {
            "latestRelease": latestRelease,
            "tourReleases": releases,
            "thisRelease": version,
        }

    buildBranch(
        "dgraph-" + latestRelease,
        "",
        jsonFor(latestRelease, latestRelease, releases))

    for r in releases:
        path = r if r == "master" else "dgraph-" + r
        buildBranch(path, path, jsonFor(r, latestRelease, releases))


def main():
    releases = getReleases()

    exec("rm", "-rf", "public")
    exec("mkdir", "public")

    buildAll(releases)

    exec("git", "checkout", "master")

    exec("rm", "-rf", "published")
    exec("mv", "public", "published")
    exec("git", "add", "published")
    # exec("git", "commit", "-m", "Hugo rebuild all branches")

main()
