# Custom HTTP server
Pet project to learn how HTTP servers work internally.




# Requirements
1. Setup [pipenv](https://pipenv.pypa.io/en/latest/) environment with `Python3.11`
2. Install dependencies: `pipenv install`


# How to run
```shell
./server.sh {--directory base-directory-name}
```


# How to add new endpoint
1. Implement new endpoint class in `src/endpoint.py`. It should be inherited from `BaseEndpoint` and implements `EndpointProtocol`.
2. Add new class instance to the `REGISTERED_ENDPOINTS`.


# How to e2e test
1. Create new file with the name test_*.sh in the directory `test/e2e/`
2. Write new test based on the template: GIVE/WHEN/THEN.
3. Run tests from the project's root directory:
```shell
export TEST_BASE_DIR=$(pwd) && test/e2e/run.sh
```


# Implemented endpoints
- `/` (Returns 200 status code).

![](demo/root.gif)

- `/echo/{message:string}` (Returns the message. The message can be encoded if `Accept-Encoding: gzip` header is provided).


- `/user-agent` (Returns the value of `User-Agent` header).


- `/files/{file-name:string}` (Returns file's content if body is empty. Creates new file based on body otherwise).
