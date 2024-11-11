import requests
import json
from typing import List, Dict

class ClinicalTrialsFetcher:
    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"

    def fetch_clinical_trials(self, condition: str, max_results: int = 5) -> dict:
        """Fetch data from ClinicalTrials.gov API"""
        try:
            params = {
                "query.cond": condition,
                "pageSize": max_results,
                "format": "json"
            }
            headers = {
                "accept": "application/json"
            }

            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None

    def parse_clinical_trials(self, response_data: dict) -> List[Dict]:
        """Parse ClinicalTrials.gov JSON response"""
        if not response_data or 'studies' not in response_data:
            return []

        trials = []

        for study in response_data['studies']:
            trial_data = {}
            protocol = study.get('protocolSection', {})

            # Basic identification info
            identification = protocol.get('identificationModule', {})
            trial_data['nct_id'] = identification.get('nctId')
            trial_data['title'] = identification.get('briefTitle')

            # Status information
            status = protocol.get('statusModule', {})
            trial_data['status'] = status.get('overallStatus')
            trial_data['start_date'] = status.get('startDateStruct', {}).get('date')

            # Sponsor information
            sponsor = protocol.get('sponsorCollaboratorsModule', {})
            trial_data['sponsor'] = sponsor.get('leadSponsor', {}).get('name')

            # Description
            description = protocol.get('descriptionModule', {})
            trial_data['brief_summary'] = description.get('briefSummary')

            # Conditions and keywords
            conditions = protocol.get('conditionsModule', {})
            trial_data['conditions'] = conditions.get('conditions', [])
            trial_data['keywords'] = conditions.get('keywords', [])

            # Study design
            design = protocol.get('designModule', {})
            trial_data['study_type'] = design.get('studyType')
            trial_data['phases'] = design.get('phases', [])
            trial_data['enrollment'] = design.get('enrollmentInfo', {}).get('count')

            # Interventions
            interventions = protocol.get('armsInterventionsModule', {}).get('interventions', [])
            trial_data['interventions'] = [
                {
                    'type': intervention.get('type'),
                    'name': intervention.get('name')
                }
                for intervention in interventions
            ]

            # Eligibility
            eligibility = protocol.get('eligibilityModule', {})
            trial_data['eligibility'] = {
                'criteria': eligibility.get('eligibilityCriteria'),
                'gender': eligibility.get('sex'),
                'min_age': eligibility.get('minimumAge'),
                'max_age': eligibility.get('maximumAge')
            }

            trials.append(trial_data)

        return trials

    def format_trial_summary(self, trials: List[Dict]) -> str:
        """Format the parsed trials into a readable summary"""
        summary = []

        for trial in trials:
            summary.append("\n=== Clinical Trial Summary ===")
            summary.append(f"NCT ID: {trial.get('nct_id', 'N/A')}")
            summary.append(f"Title: {trial.get('title', 'N/A')}")
            summary.append(f"Status: {trial.get('status', 'N/A')}")
            summary.append(f"Start Date: {trial.get('start_date', 'N/A')}")
            summary.append(f"Sponsor: {trial.get('sponsor', 'N/A')}")

            if trial.get('conditions'):
                summary.append(f"Conditions: {', '.join(trial['conditions'])}")

            if trial.get('keywords'):
                summary.append(f"Keywords: {', '.join(trial['keywords'])}")

            if trial.get('phases'):
                summary.append(f"Phase: {', '.join(trial['phases'])}")

            summary.append(f"Enrollment: {trial.get('enrollment', 'N/A')} participants")

            if trial.get('interventions'):
                summary.append("\nInterventions:")
                for intervention in trial['interventions']:
                    summary.append(f"- {intervention['type']}: {intervention['name']}")

            if trial.get('brief_summary'):
                summary.append("\nBrief Summary:")
                summary.append(trial['brief_summary'])

            summary.append("\nEligibility:")
            eligibility = trial.get('eligibility', {})
            summary.append(f"Gender: {eligibility.get('gender', 'N/A')}")
            summary.append(f"Age: {eligibility.get('min_age', 'N/A')} - {eligibility.get('max_age', 'N/A')}")

            summary.append("\n")

        return "\n".join(summary)

    def fetch_and_summarize_trials(self, condition: str, max_results: int = 5) -> str:
        """Fetch clinical trials data and return a formatted summary"""
        response_data = self.fetch_clinical_trials(condition, max_results)
        if response_data:
            trials = self.parse_clinical_trials(response_data)
            return self.format_trial_summary(trials)
        return "No results found or error occurred"