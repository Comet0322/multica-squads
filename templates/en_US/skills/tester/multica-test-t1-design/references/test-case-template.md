# Test Case Templates

## Executable + traceable (mandatory reminder)

- Write preconditions as "Log in with an account that has {the specific permission of this system}": **do not hard-code personal accounts/passwords**; also **do not leave a literal XXX** — the Agent identifies the permission name for the current system
- Steps use real menu paths and test-data aliases; expected results map back to AC/PRD
- See the field notes in `multica-test-t1-design/SKILL.md` and [`design-trace.md`](design-trace.md)

## Functional test case template

```
=== Functional Test Case ===

Case ID: TC-F-{module}-{sequence}
Module: {system/business domain/feature module, layered with /}
Test title: {concise description of the test scenario}
Preconditions:
  1. Log in with an account that has the [{module/operation}] permission
  2. Test data: {alias}={key field values}
  3. {Data is ready / calculation can be triggered}
Test data: {key inputs corresponding to AC}
Case type: [UI check / Functional flow / Input validation / Boundary value / Exception scenario]
Priority:  [P1 core / P2 normal / P3 exception or boundary] (never default to P0)
Traceability: [{JIRA AC or PRD clause}]

Test steps:
1. Go to {system} -> {menu path}, wait for loading to finish
2. {business operation}
3. {verify the result}

Expected results:
1. {expected result of step 1}
2. {expected result of step 2}
3. {expected result of step 3}
---
```

### Functional test case example (permissioned login + executable path)

```
=== Functional Test Case ===

Case ID: TC-F-CROSSBITE-001
Module: Module B/Status Tags/Order Query and Tagging
Test title: Tag A is applied successfully and searchable when Count>0 and field X is greater than 1mm
Preconditions:
  1. Log in with an account that has the Module B [Order Query] permission
  2. Test data: order A_ant_ok, order Count=2 and field X=1.5
  3. Tag calculation has completed
Test data: Count_front=2, field X=1.5 (AC scenario A)
Case type: Functional flow
Priority: P1
Traceability: PROJ-123 AC-A

Test steps:
  1. Go to System A -> Module B -> Order Query, wait for loading to finish
  2. Select the [Tag A] tag (if the page says [Tag A] use the actual wording), wait for the order square to refresh
  3. Search by order number A_ant_ok and check the tag

Expected results:
  1. The Order Query page opens
  2. The tag is selected and the list refreshes successfully
  3. The order appears in the results and shows the [Tag A] tag
---
```

---

## API test case template

```
=== API Test Case ===

Case ID: TC-I-{module}-{sequence}
API name: {method} {API URL}
Test title: {concise description of the test scenario}
Request method: GET/POST/PUT/DELETE
Preconditions: {1. 2. 3.}

Request parameters:
  {param name}: {param value}  // {description}

Expected status code: {HTTP status code}
Expected business code: {business code (if any)}

Expected response body:
```json
{
  "field_validation_note": ""
}
```

Checkpoints:
  - {point 1: e.g. "the status field value should be success"}
  - {point 2: e.g. "the data field should be of array type"}
---
```

### API test case example

```
=== API Test Case ===

Case ID: TC-I-USER-001
API name: POST /api/v1/user/login
Test title: Verify login with the correct account and password returns success
Request method: POST
Preconditions:
  1. The test account is registered and in normal status (account taken from the test-data config, no hard-coded personal account)
  2. The service is running normally

Request parameters:
  {
    "email": "<test_account_email>",
    "password": "<from_secure_test_config>"
  }

Expected status code: 200
Expected business code: 0 (business success)

Expected response body:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "<string, JWT token>",
    "userInfo": {
      "userId": "<number>",
      "nickname": "<string>",
      "avatar": "<string, URL>",
      "email": "<string>"
    }
  }
}
```

Checkpoints:
  - code = 0, meaning business success
  - message = "success"
  - data.token is a non-empty string
  - data.userInfo.userId is a number
  - data.userInfo.email matches the request parameter
  - Returned fields match the API doc, none missing and none extra
---
```
