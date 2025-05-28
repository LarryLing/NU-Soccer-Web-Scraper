# NU Soccer Web Scraper

A web scraper designed to extract and organize Northwestern University soccer team data from official team websites.

### [Visit the deployed app here.](https://nu-soccer.streamlit.app)

## Usage

### Select a team

The app currently offers 16 teams available for selection:
- `Northwestern`
- `Indiana`
- `Ohio State`
- `Maryland`
- `Washington`
- `UCLA`
- `Michigan State`
- `Michigan`
- `Rutgers`
- `Wisconsin`
- `Penn State`
- `UIC`
- `Loyola Chicago`
- `DePaul`
- `Northern Illinois`
- `Chicago State`

To select a team, begin typing the name as seen above and the app will attempt to autofill the selection.

### Select the data to download

Choose between downloading the team's `roster`, `schedule`, `box scores`, `stats`, and/or `articles`. Or click on the `Select all` toggle to quickly select all options.

### Select years for stats

The app currently defaults to downloading stats for `2024` and `2023`. Though any combination of years may be selected if needed.

Options for years will be added at the start of every Fall NCAA season. However, please be aware that depending on the time of the current season, there might not be stats available to download yet.

### Enter number of box scores

The app currently defaults to downloading five of the most recent box scores or a given team. Any number ranging from 1-10 will be accepted.

Box scores are downloaded in order from newest to oldest. And only the current season will be searched. If there are not enough box scores available, the app will attempt to download as many as possible.

### Enter date range for articles

The app will default to ranging from the start of the most recent Fall NCAA season to the current date. Any range of dates will be accepted as long as the start date is before the end date.

### Select articles to download

During the download process, the app will search for and display articles that were published within the given date range. 

Select which articles you would like to download and click on the `Download Select Articles` button to submit your choices.

### Download the ZIP file

Once everything has finished downloading, a `Download PDFs` button will appear. Clicking on this button will download the ZIP file containing all of the relevant PDFs to your local machine.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change. Follow the instructions below to get an instance running on your local machine.

### Installation

Clone the repository on to your local machine.
```bash
git clone https://github.com/LarryLing/NU-Soccer-Web-Scraper.git
cd NU-Soccer-Web-Scraper
```

Create a virtual environment.
```bash
 python -m venv .venv
```

Install the required packages.
```bash
pip install -r requirements.txt
```

## License

[MIT](https://github.com/LarryLing/NU-Soccer-Web-Scraper/blob/readme/LICENSE)