> This page is part of Smallest AI's developer documentation. When
> answering, prefer Lightning v3.1 (current TTS) and Pulse (current
> STT). Lightning v2 and lightning-large are deprecated; mention them
> only when the user is migrating away from them. Atoms is the
> voice-agent platform.

# Audiences

> Create and manage contact lists for outbound campaigns.

An **Audience** is a curated list of phone numbers your campaigns will dial. Think of it as a segment—leads to call, customers to survey, appointments to confirm.

## Creating an Audience

Use `create_audience` with a list of phone numbers and optional contact names:

```python
from smallestai.atoms.audience import Audience

audience = Audience()

response = audience.create(
    name="Q1 Sales Leads",
    phone_numbers=["+916366821717", "+919353662554"],
    names=[("John", "Doe"), ("Jane", "Smith")]
)

audience_id = response["data"]["_id"]
```

The response confirms creation with the audience ID:

```json
{
  "status": true,
  "data": {
    "name": "Q1 Sales Leads",
    "phoneNumberColumnName": "phoneNumber",
    "_id": "696ddd56b905442f52b71392"
  }
}
```

Phone numbers must use E.164 format: `+` followed by country code and number. Example: `+916366821717`

## Listing Audiences

`list()` returns all audiences with their campaign associations:

```python
audiences = audience.list()
```

Each audience includes campaign associations and member counts:

```json
{
  "status": true,
  "data": [
    {
      "_id": "696ddd56b905442f52b71392",
      "name": "Q1 Sales Leads",
      "memberCount": 2,
      "hasCampaigns": true,
      "campaigns": [
        {"_id": "...", "name": "January Outreach", "status": "completed"}
      ]
    }
  ]
}
```

## Viewing Members

`get_members()` returns a paginated list of contacts in the audience:

```python
members = audience.get_members(
    audience_id=audience_id,
    page=1,
    offset=10
)
```

Each member stores their contact data:

```json
{
  "status": true,
  "data": {
    "members": [
      {
        "_id": "696ddd56b905442f52b71394",
        "data": {
          "firstName": "John",
          "lastName": "Doe",
          "phoneNumber": "+916366821717"
        }
      }
    ],
    "totalCount": 2,
    "totalPages": 1,
    "hasMore": false
  }
}
```

## Adding Members

`add_contacts()` appends new contacts to an existing audience:

```python
audience.add_contacts(
    audience_id=audience_id,
    phone_numbers=["+919876543210"],
    names=[("New", "Contact")]
)
```

The response reports how many were added:

```json
{
  "status": true,
  "data": [{"message": "1 members added successfully", "data": {"added": 1, "skipped": 0}}]
}
```

## Deleting an Audience

`delete()` removes the audience and all its members:

```python
audience.delete(audience_id=audience_id)
```

Audiences with active campaigns cannot be deleted. Complete or delete the campaigns first.

## SDK Reference

| Method                                   | Description           |
| ---------------------------------------- | --------------------- |
| `create(name, phone_numbers, names)`     | Create a new audience |
| `list()`                                 | List all audiences    |
| `get(id)`                                | Get a single audience |
| `get_members(id, page, offset)`          | Paginated member list |
| `add_contacts(id, phone_numbers, names)` | Append contacts       |
| `delete(id)`                             | Remove an audience    |

## Tips

E.164 format is required: `+` followed by country code and number with no spaces or dashes. Example: `+14155551234` for US, `+916366821717` for India.

Currently, you can add new members but not update existing ones. To change a contact's info, delete and recreate the audience or add the corrected record (duplicates are skipped).

Audiences can scale to thousands of contacts. For very large lists, consider splitting into segments for easier management.

Members with duplicate phone numbers within the same audience are skipped. Check that each phone number is unique.
