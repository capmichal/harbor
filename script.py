import requests
from datetime import datetime, timedelta

# structure = projects --> repositories --> artifacts

# Harbor API information
harbor_base_url = 'http://192.168.56.101/api/v2.0'
username = 'admin'
password = 'Harbor12345'

# Make a GET request with basic authentication
repositories_endpoint = f'{harbor_base_url}/repositories' # general repositories, weird PROJECT/REPO NAMES
projects_endpoint = f'{harbor_base_url}/projects' # 

current_time = datetime.now() # variable used to determine how old images are


""" # CURRENTLY UNUSED
def repos(): #handling repos
    response = requests.get(repositories_endpoint, auth=(username, password))

    if response.status_code == 200:
        repositories = response.json()
        for repository in repositories: # currently listing projects not repositories
            print(repository)

            if repository["name"] == "library/nginx": # wiecej info o danym repo
                print(f"dowiaduje sie wiecej o {repository['name']}")
                # po delete nie dostajemy JSONa
                #specRepoResponse = requests.delete(f'http://192.168.56.101/api/v2.0/projects/library/repositories/nginx', auth=(username, password)) # WORKING DELETION
                specRepoResponse = requests.get(f'http://192.168.56.101/api/v2.0/projects/library/repositories/nginx', auth=(username, password))

    else:
        print(f"Failed to fetch repositories. Status code: {response.status_code}")
        print(f"Response: {response.text}")

def projects():
    response = requests.get(projects_endpoint, auth=(username, password))
    
    if response.status_code == 200:
        projects = response.json()
        for project in projects:
            print("PROJEKT")
            print(project)

        # listing repositories only from specific projects (TODO vip and daisy projects)
        

    else:
        print("Problem with fetching projects")
"""

def specRepo(project_name, dryRun=True): # operating only inside specific project
    specRepoEndpoint = f'{harbor_base_url}/projects/{project_name}/repositories'
    response = requests.get(specRepoEndpoint, auth=(username, password))

    if response.status_code == 200:
        repositories = response.json()
        for repository in repositories: # operating on all repos from specific project

            formattedRepoName = repository["name"].split("/")[1] # otherwise reponame is "project_name/repo_name"
            
            if repository["artifact_count"] > 0: # works, only interested with repos with huge artifacts number  
                created = datetime.strptime(repository["creation_time"], "%Y-%m-%dT%H:%M:%S.%fZ")
                print(f"{repository['name']} this repo was created on {created}, to są jego artefakty: ")

                artifactsEndpoint = f"{harbor_base_url}/projects/{project_name}/repositories/{formattedRepoName}/artifacts"
                artifacts = requests.get(artifactsEndpoint, auth=(username, password)).json()
                for art in artifacts:
                    for tag in art["tags"]:
                        if dryRun == True:
                            print(tag["name"])
                        elif dryRun == False:
                            print(tag["name"])
                            if tag["name"] == "edge":
                                print(f"deleting artifact with tag {tag['name']}")
                                delete = requests.delete(f"{artifactsEndpoint}/{tag['name']}", auth=(username, password))
            # FUNKCJONALNOŚĆ Z KONTROLĄ "NOWOŚCI" repozytorium, można włączyć DZIAŁA    
            # time_difference = current_time - created
            # if time_difference > timedelta(hours=1): # checking how old repository is
            #     print("repo zrobione dawniej niz 3.5h temu")


    else:
        print(f"Failed to fetch repositories. Status code: {response.status_code}")
        print(f"Response: {response.text}")


specRepo("projekt3", dryRun=False)