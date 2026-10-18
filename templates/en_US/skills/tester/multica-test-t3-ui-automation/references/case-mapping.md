# Functional case -> UI one-to-one mapping

## Count

`N = len(json["functional"])`  
Generate `N` test functions; the collected count at execution must be `N`.

`case_id` -> method name: replace non-alphanumeric characters with `_` so it is valid and unique.

## Steps

| Functional case field | UI script |
| --- | --- |
| `preconditions` | fixture or start of the test; login wording uses permission semantics, passwords are read only from environment variables |
| `steps[i]` | one Playwright action (click/fill/select/wait) |
| `expected_results[i]` | `expect(...)` or `assert`; placed right after the step inside the same test |

## Locators

Priority: `get_by_role` -> `get_by_label` -> `get_by_text` -> `get_by_placeholder`.  
No CSS selectors without a basis on the page.  
Opened `page_url` and still cannot find it -> `@pytest.mark.blocked` + skip.

## Do not

- Write "API returns 200" as a UI assertion (unless the step is literally to look at an on-page message)
- Drop steps just to make the run pass
- Share mutable global state across cases
