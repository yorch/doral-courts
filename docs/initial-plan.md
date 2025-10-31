# Doral Courts CLI App

This is a command-line interface (CLI) application for showing information about Doral Tennis and Pickleball Courts availability.

## Features

- Display available courts for tennis and pickleball
- Show court details such as location, surface type, and availability status
- Allow users to filter courts by sport type and availability
- Provide real-time updates on court availability

## Technologies

- Python for the backend logic
- SQLite for the database
- `uv` for managing the application lifecycle and dependencies

## Data

- The information can be obtained from the Doral Tennis and Pickleball Courts website.
- An HTTP request to load the page with the looks like:

```bash
curl 'https://fldoralweb.myvscloud.com/webtrac/web/search.html?Action=Start&SubAction=&_csrf_token=bd6C086V0M1K2M38143J274U4Q4X5C531O6W606P6T0H5R515U6K0Y613P4C571I065R5B531T074S5O4F0C5B52473Y1E5R6950591I09656S6U6I005J5P5G0C5P4R5F&date=07%2F12%2F2025&begintime=08%3A00+am&type=Pickleball+Court&type=Tennis+Court&subtype=&category=&features=&keyword=&keywordoption=Match+One&blockstodisplay=24&frheadcount=0&primarycode=&features1=&features2=&features3=&features4=&features5=&features6=&features7=&features8=&display=Detail&search=yes&page=1&module=fr&multiselectlist_value=&frwebsearch_buttonsearch=yes' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'cache-control: max-age=0' \
  -b '_CookiesEnabled=Yes; _mobile=no; _webtracsessionid=e6b4c0cbfbe5f0b0ffe7a15c78f56355648d0dc077c0e984a5542c054bae8d344df34b2a04adbe59b6c1bcc4b6c22b0248b5aed22223d5b3b8f315086f779920; __cf_bm=HvTCvRId1MPeSf6ZPqtrThnoGNt1ofyyWSw9_rKLdlQ-1752274951-1.0.1.1-P7mTGeiUUN6pYtY2tJfI_FGWR_luOWMDB61gSxMEmcb_fkgBc3g4UK5JNywMRH1qq1NbwflhcvxyYpajLdiY69uer1WHnTynq2_JWoyNREQ' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
```

- A subsequent request to load the next page of results looks like this:

```bash
curl 'https://fldoralweb.myvscloud.com/webtrac/web/search.html?Action=Start&SubAction=&_csrf_token=cD6L6X6V0A6R4424214T2J3M5P4U585L085L4G6T6C710B3L6U56034R4V5B4Z0M5Q4M6D6K1E5E6A476K1L5S3O6R6I6Z4T606H4X0F6Y4K5P5I0G5X4J4D521G5M585B&date=07%2F12%2F2025&begintime=08%3A00+am&type=Pickleball+Court&type=Tennis+Court&subtype=&category=&features=&keyword=&keywordoption=Match+One&blockstodisplay=24&frheadcount=0&primarycode=&features1=&features2=&features3=&features4=&features5=&features6=&features7=&features8=&display=Detail&search=yes&page=2&module=fr&multiselectlist_value=' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
  -H 'accept-language: en-US,en;q=0.9' \
  -b '_CookiesEnabled=Yes; _mobile=no; _webtracsessionid=e6b4c0cbfbe5f0b0ffe7a15c78f56355648d0dc077c0e984a5542c054bae8d344df34b2a04adbe59b6c1bcc4b6c22b0248b5aed22223d5b3b8f315086f779920; __cf_bm=HvTCvRId1MPeSf6ZPqtrThnoGNt1ofyyWSw9_rKLdlQ-1752274951-1.0.1.1-P7mTGeiUUN6pYtY2tJfI_FGWR_luOWMDB61gSxMEmcb_fkgBc3g4UK5JNywMRH1qq1NbwflhcvxyYpajLdiY69uer1WHnTynq2_JWoyNREQ' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
```
