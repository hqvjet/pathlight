import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

EXCHANGE_RATE_API = os.getenv('EXCHANGE_RATE_API_URL', 'https://api.exchangerate.host/latest?base=USD&symbols=VND')
USD_TO_VND_FALLBACK = 25000


def get_usd_to_vnd_rate() -> float:
    try:
        request = Request(EXCHANGE_RATE_API, headers={'User-Agent': 'pathlight-service'})
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read())
        return float(payload['rates']['VND'])
    except (KeyError, TypeError, ValueError, HTTPError, URLError, TimeoutError) as exc:
        logger.warning("Falling back to default USD/VND rate: %s", exc)
        return float(os.getenv('USD_TO_VND_FALLBACK', USD_TO_VND_FALLBACK))


def get_aws_costs_last_30_days() -> Dict:
    """
    Get AWS costs for the last 30 days using boto3 Cost Explorer API
    Returns costs in VND
    """
    try:
        # Initialize Cost Explorer client
        ce_client = boto3.client('ce', region_name='us-east-1')
        
        # Calculate date range (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Format dates for AWS API (YYYY-MM-DD)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Get cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_str,
                'End': end_str
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        usd_to_vnd = get_usd_to_vnd_rate()
        costs = []
        total_cost_usd = 0.0
        
        for result in response.get('ResultsByTime', []):
            date_str = result['TimePeriod']['Start']
            # Parse date and format as DD/MM/YYYY
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
            
            # Get cost in USD
            cost_usd = float(result['Total']['UnblendedCost']['Amount'])
            # Convert to VND
            cost_vnd = cost_usd * usd_to_vnd
            
            costs.append({
                'date': formatted_date,
                'cost': round(cost_vnd, 2)
            })
            
            total_cost_usd += cost_usd

        total_cost_vnd = round(total_cost_usd * usd_to_vnd, 2)

        return {
            'status': 200,
            'total_cost': total_cost_vnd,
            'costs': costs
        }
    except ClientError as e:
        logger.error(f"AWS Cost Explorer error: {e}")
        return {
            'status': 500,
            'message': f"Lỗi khi lấy thông tin chi phí từ AWS: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error getting AWS costs: {e}")
        return {
            'status': 500,
            'message': "Có lỗi xảy ra khi lấy thông tin chi phí"
        }
