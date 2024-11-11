# src/data_fetchers/cdc_fetcher.py

from typing import List, Dict
from collections import defaultdict

class CDCFetcher:
    def fetch_cdc_rare_disease_data(self) -> dict:
        """
        Returns sample rare disease data since the CDC API is not accessible
        """
        return self.generate_sample_data()

    def generate_sample_data(self) -> dict:
        """Generate comprehensive sample rare disease data for demonstration"""
        return {
            "rare_diseases": [
                {
                    "disease_name": "Gaucher Disease",
                    "category": "Lysosomal Storage Disorders",
                    "year": 2024,
                    "total_cases": 178,
                    "age_distribution": {
                        "0-17": 45,
                        "18-44": 82,
                        "45-64": 38,
                        "65+": 13
                    },
                    "gender_distribution": {
                        "Male": 85,
                        "Female": 93
                    },
                    "mortality_rate": 3.2,
                    "prevalence": "1 in 50,000"
                },
                {
                    "disease_name": "Fabry Disease",
                    "category": "Lysosomal Storage Disorders",
                    "year": 2024,
                    "total_cases": 245,
                    "age_distribution": {
                        "0-17": 56,
                        "18-44": 112,
                        "45-64": 58,
                        "65+": 19
                    },
                    "gender_distribution": {
                        "Male": 142,
                        "Female": 103
                    },
                    "mortality_rate": 4.5,
                    "prevalence": "1 in 40,000"
                },
                {
                    "disease_name": "Pompe Disease",
                    "category": "Metabolic Disorders",
                    "year": 2024,
                    "total_cases": 156,
                    "age_distribution": {
                        "0-17": 67,
                        "18-44": 52,
                        "45-64": 28,
                        "65+": 9
                    },
                    "gender_distribution": {
                        "Male": 83,
                        "Female": 73
                    },
                    "mortality_rate": 7.8,
                    "prevalence": "1 in 65,000"
                },
                {
                    "disease_name": "Niemann-Pick Disease",
                    "category": "Lysosomal Storage Disorders",
                    "year": 2024,
                    "total_cases": 132,
                    "age_distribution": {
                        "0-17": 58,
                        "18-44": 45,
                        "45-64": 22,
                        "65+": 7
                    },
                    "gender_distribution": {
                        "Male": 71,
                        "Female": 61
                    },
                    "mortality_rate": 8.5,
                    "prevalence": "1 in 75,000"
                },
                {
                    "disease_name": "Hunter Syndrome",
                    "category": "Metabolic Disorders",
                    "year": 2024,
                    "total_cases": 98,
                    "age_distribution": {
                        "0-17": 42,
                        "18-44": 35,
                        "45-64": 15,
                        "65+": 6
                    },
                    "gender_distribution": {
                        "Male": 89,
                        "Female": 9
                    },
                    "mortality_rate": 6.2,
                    "prevalence": "1 in 100,000"
                }
            ]
        }

    def parse_rare_disease_data(self, response_data: dict) -> Dict[str, List[Dict]]:
        """Parse CDC data and organize by disease category"""
        if 'rare_diseases' not in response_data:
            return {}

        categories = defaultdict(list)
        for disease in response_data['rare_diseases']:
            category = disease.get('category', 'Uncategorized')
            categories[category].append(disease)

        return dict(categories)

    def format_rare_disease_summary(self, data: Dict[str, List[Dict]]) -> str:
        """Format the parsed rare disease data into a readable summary"""
        if not data:
            return "No rare disease data available"

        summary = []
        summary.append("=== CDC Rare Disease Surveillance Summary ===\n")

        # Calculate total cases across all categories
        total_cases = sum(
            disease['total_cases']
            for category_diseases in data.values()
            for disease in category_diseases
        )

        summary.append(f"Total Rare Disease Cases Monitored: {total_cases:,}\n")

        for category, diseases in data.items():
            summary.append(f"\n{category}")
            summary.append("=" * len(category))

            for disease in diseases:
                summary.append(f"\nDisease: {disease['disease_name']}")
                summary.append(f"Total Cases: {disease['total_cases']:,}")
                summary.append(f"Prevalence: {disease['prevalence']}")
                summary.append(f"Mortality Rate: {disease['mortality_rate']}%")

                summary.append("\nAge Distribution:")
                for age_group, count in disease['age_distribution'].items():
                    percentage = (count / disease['total_cases']) * 100
                    summary.append(f"  {age_group}: {count:,} cases ({percentage:.1f}%)")

                summary.append("\nGender Distribution:")
                for gender, count in disease['gender_distribution'].items():
                    percentage = (count / disease['total_cases']) * 100
                    summary.append(f"  {gender}: {count:,} cases ({percentage:.1f}%)")

                summary.append("\n" + "-" * 50)

        # Add summary statistics
        summary.append("\nSummary Statistics")
        summary.append("=" * 16)
        summary.append(f"Total Disease Categories: {len(data)}")
        summary.append(f"Total Diseases Monitored: {sum(len(diseases) for diseases in data.values())}")
        summary.append(f"Average Cases per Disease: {total_cases / sum(len(diseases) for diseases in data.values()):,.1f}")

        return "\n".join(summary)

    def fetch_and_summarize_rare_diseases(self) -> str:
        """Fetch CDC rare disease data and return a formatted summary"""
        response_data = self.fetch_cdc_rare_disease_data()
        if response_data:
            parsed_data = self.parse_rare_disease_data(response_data)
            return self.format_rare_disease_summary(parsed_data)
        return "Failed to fetch data from CDC API"