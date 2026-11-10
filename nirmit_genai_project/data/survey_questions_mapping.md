# Google Forms → Consumer research fields

This project recognizes the 15 original Google Forms questions from the group's draft:

| User question | Normalized field |
|---|---|
| Discretionary spending budget | `budget` |
| Energy drinks consumed per week/month | `frequency`, parsed to `weekly_drinks` only when unambiguous |
| Days and activities | `activities` |
| Reasons for consuming | `motivations` |
| Reasons for skipping | `skip_conditions` |
| Brands purchased and shares | `brand_shares` (text retained; first detected brand is provisional favorite) |
| Three favorite products and flavor/size | `favorites` |
| Product likes | `likes` |
| Regular versus sugar-free | `sugar` |
| Unavailable favorite fallback | `fallback` |
| Purchase locations | `channel` |
| Normal price | `usual_price` |
| Highest price | `max_price` |
| 25% increase response | `price_response` (weak inferred label, excluded from statistical training) |
| Discounts, promotions and bulk deals | `promotions` |

Suggested **optional additions**: age group, student status, actual purchases in last 7 days, explicit 25% price choice (same/less/switch/quit), numeric expected drinks/week *after* increase, and actual follow-up purchases. Do not upload identifiable participant information to public repositories. Obtain participant permission for third-party AI processing.

CSV import accepts the original Google Forms question labels; fields not recognized remain in `raw_answers` and are never silently filled.
