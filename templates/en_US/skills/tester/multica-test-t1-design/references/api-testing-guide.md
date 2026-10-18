# API Testing Guide

## Common Web API test scenario templates

### 1. Login/authentication APIs

**Typical endpoints:** `POST /api/v1/login` `POST /api/v1/register` `POST /api/v1/refresh-token`

**Validation points:**
| Test scenario | Input | Expected |
|---------|------|------|
| Correct credentials | Correct user/pass | 200 + token |
| Wrong password | Correct user / wrong pass | 401 + error message |
| Non-existent user | Unregistered user | 401 + corresponding message |
| Empty username | Omitted or empty | 400 + parameter validation message |
| Empty password | Omitted or empty | 400 + parameter validation message |
| Overlong field | 1000-character username | 400 + length limit message |
| SQL injection | `admin' OR 1=1--` | Login fails, not bypassed |
| Locked account | Locked after repeated failures | 403 + lockout message |

### 2. CRUD resource APIs

**Typical endpoints:** `GET/POST/PUT/DELETE /api/v1/resources/{id}`

**Validation points:**
| Test scenario | Input | Expected |
|---------|------|------|
| Query succeeds | Valid ID | 200 + full resource data |
| Resource not found | Non-existent ID | 404 + corresponding code |
| Invalid ID format | Letters / negative ID | 400 |
| Create succeeds | Complete valid parameters | 201 + created resource |
| Missing required field | Omitted | 400 + field message |
| Create duplicate data | Existing unique constraint | 409/400 |
| Update succeeds | Valid data | 200 + updated resource |
| Update non-existent resource | Non-existent ID | 404 |
| Delete succeeds | Existing ID | 204/200 |
| Delete non-existent resource | Non-existent ID | 404 |

### 3. List/pagination APIs

**Typical endpoint:** `GET /api/v1/resources`

**Validation points:**
| Test scenario | Input | Expected |
|---------|------|------|
| Default pagination | page/pageSize omitted | Default first page, default page size |
| Specified pagination | page=2, pageSize=10 | Correct page data |
| pageSize boundary | Minimum 1, maximum 100 | Correct |
| pageSize out of range | pageSize=0 or pageSize=10000 | Falls back to default or maximum |
| Negative page | page=-1 | Falls back to default or errors |
| Sorting | sort=field, order=asc/desc | Correctly sorted result |
| Filtering | Condition parameters | Filtered result correct |
| Total count | total field matches actual count | Consistent |
| Empty result | Non-existent filter condition | Empty array + total=0 |

### 4. File upload APIs

**Typical endpoint:** `POST /api/v1/upload`

**Validation points:**
| Test scenario | Input | Expected |
|---------|------|------|
| Upload succeeds | File of allowed format/size | 200 + file URL |
| Unsupported format | .exe or other disallowed formats | 400 + format error message |
| File too large | Exceeds the limit | 413 + size limit message |
| Empty file | 0-byte file | 400 + message |
| No file | File not sent | 400 |
| Large-file boundary | File size exactly equal to the limit | Success or a clear message |
| Special characters in file name | Chinese/space/emoji file names | Handled correctly |

---

## Response field validation methodology

### Field-by-field validation flow

For each API's response body, run the following flow:

```
For each field in the response:
  1. Field presence -- are all fields defined in the docs returned?
  2. Field type -- does the type match what is actually returned?
     - string: is the returned value a string (a numeric string still counts as a string)
     - number: integer or float, and is the precision correct
     - boolean: true/false or 0/1
     - array: an array rather than null or something else
     - object: an object with the correct format
  3. Field value range -- is the value within the range allowed by the business
  4. Boundary conditions -- maximum, minimum, extremely long strings
  5. null/empty values -- when the field has no data, does it return null, an empty string, or omit the field
  6. Format -- date format, URL format, enum value spelling
```

### Common response structure example and validation

```json
{
  "code": 0,                    // number, business status code; verify all enum values
  "message": "success",         // string, message text, Chinese or English
  "data": {
    "id": 10001,               // number, always a positive integer
    "name": "Test Product",    // string, 1-50 characters
    "price": "99.99",          // string (amounts use strings to avoid precision issues)
    "status": 1,               // number, enum value 0|1|2
    "createdAt": "2026-05-31T10:00:00Z", // string, ISO 8601 format
    "tags": ["tag1", "tag2"],  // array of string, may be an empty array []
    "extra": null              // object or null, null when there is no extra data
  }
}
```

### Common business status code reference

| Business code | Meaning | Description |
|--------|------|------|
| 0 | Success | Request processed successfully |
| 1001 | Invalid parameter | Request parameter validation failed |
| 1002 | Unauthorized | Not logged in or token invalid |
| 1003 | Forbidden | Logged in but no permission for the operation |
| 1004 | Resource not found | The requested resource does not exist |
| 1005 | Resource conflict | Duplicate submission / data already exists |
| 1006 | Server error | System exception |
| 1007 | Rate limited | Too many requests |
