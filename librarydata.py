import os
import requests
import pandas as pd
import dotenv
from sqlalchemy import create_engine
import seaborn as sns
import matplotlib.pyplot as plt

# Load environment variables from .env file
dotenv.load_dotenv()


# Fetching books from the provided API URL and returning a list of book data
class BookFetcher:
    def __init__(self, API_URL):
        self.api_url = API_URL

    def extract_books(self):
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()
            return data.get("docs", [])
        except requests.RequestException as e:
            print(f"Error fetching books: {e}")
            return []


# Cleaning and transforming the book data
class BookCleaner:
    def __init__(self, list_of_json_data):
        self.data = list_of_json_data
        self.cleaned_data = None

    def clean_data(self):
        cleaned_data = []
        for item in self.data:
            flattened_item = {
                "title": item.get("title", ""),
                "author_name": ", ".join(item.get("author_name", [])),
                "first_publish_year": item.get("first_publish_year", ""),
                "ratings": item.get("ratings_sortable", ""),
            }
            cleaned_data.append(flattened_item)
        self.cleaned_data = pd.DataFrame(cleaned_data)
        return self.cleaned_data

    def save_data_into_csv(self, filename):
        self.cleaned_data.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

    def save_data_into_json(self, filename):
        self.cleaned_data.to_json(filename, orient="records")
        print(f"Data saved to {filename}")


# Loads the database connection and creates a SQLAlchemy engine for database interactions
class BookDatabase:
    def __init__(self, df):
        self.conn_url = os.getenv("DB_CONN_URL")
        if not self.conn_url:
            raise ValueError("No connection URL found in environment variables")
        self.engine = create_engine(self.conn_url)
        self.df = df

    def dataframe_to_db(self):
        self.df.to_sql("LibBooks", self.engine, if_exists="replace", index=False)
        print("Data inserted into the database.")

    def query(self, query):
        try:
            df_from_db = pd.read_sql(query, self.engine)
            print(df_from_db.head())
        except Exception as e:
            print(f"Error querying the database: {e}")


# The BookVisualizer class is responsible for creating visualizations of book data.
class BookVisualizer:
    def __init__(self, dataframe):
        self.df = dataframe

    def plot_publish_year_count(self):
        output_dir = "Visualizations"
        os.makedirs(output_dir, exist_ok=True)

        plt.figure(figsize=(12, 8))
        sns.countplot(data=self.df, x="first_publish_year", palette="coolwarm")
        plt.title("Number of Books by First Publish Year")
        plt.xlabel("First Publish Year")
        plt.ylabel("Number of Books")
        plt.xticks(rotation=45)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()

        output_path = os.path.join(output_dir, "countplot.png")
        plt.savefig(output_path)
        plt.close()
        print(f"Plot saved to {output_path}")


def main():
    API_URL = "https://openlibrary.org/search.json?q=fiction&sort=rating&fields=title,author_name,first_publish_year,ratings_sortable&limit=100"

    # Fetching the books from the provided API URL
    fetcher = BookFetcher(API_URL)
    books = fetcher.extract_books()

    # Clean and save the fetched book data to CSV and JSON files
    cleaner = BookCleaner(books)
    cleaned_df = cleaner.clean_data()
    cleaner.save_data_into_csv("books_cleaned.csv")
    cleaner.save_data_into_json("books.json")

    # Insert the cleaned data into the database and query it
    db = BookDatabase(cleaned_df)
    db.dataframe_to_db()

    query = """
        SELECT * FROM LibBooks;
    """
    db.query(query)

    # Generate a plot of the count of books by their first publish year
    visualizer = BookVisualizer(cleaned_df)
    visualizer.plot_publish_year_count()


if __name__ == "__main__":
    main()
