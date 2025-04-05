import streamlit as st
from backend.utils.budget import BudgetTracker
from backend.utils.notifications import generate_notifications
import pandas as pd
import altair as alt
from dateutil import parser as date_parser
import datetime
import openai
from backend.utils.config import Config
import json
from frontend.components.AccountSelector import show_account_selector

def categorize_transactions(transactions):
    """Use OpenAI to categorize transactions and suggest budgets."""
    try:
        # Get OpenAI API key
        api_key = Config.get_openai_api_key()
        openai.api_key = api_key

        # Calculate total spending per transaction name
        spending_summary = {}
        for tx in transactions:
            name = tx["name"]
            amount = abs(float(tx["amount"]))
            if name in spending_summary:
                spending_summary[name]["total"] += amount
                spending_summary[name]["count"] += 1
            else:
                spending_summary[name] = {"total": amount, "count": 1}

        # Prepare transaction data for OpenAI
        transaction_list = [
            {
                "name": tx["name"],
                "amount": abs(float(tx["amount"])),
                "date": tx["date"],
                "existing_category": tx.get("category", [""])[0] if isinstance(tx.get("category"), list) else tx.get("category", ""),
                "monthly_frequency": spending_summary[tx["name"]]["count"],
                "monthly_total": spending_summary[tx["name"]]["total"]
            }
            for tx in transactions
        ]

        # Create prompt for OpenAI
        prompt = f"""Analyze these financial transactions and create a smart categorization system with practical budget suggestions.

        Task 1 - Category Analysis:
        1. Look at the existing_category field in each transaction
        2. Identify the main categories and subcategories being used
        3. Maintain the existing categorization structure where possible
        4. Group similar transactions together

        Task 2 - Budget Suggestions:
        For each category, suggest a practical monthly budget following these rules:
        1. For small regular expenses (food, entertainment, etc.):
           - Round to nearest $5 if under $50
           - Round to nearest $10 if under $100
           - Round to nearest $50 if under $500
        
        2. For large expenses (rent, mortgage, etc.):
           - Round to nearest $100
        
        3. Consider these factors:
           - Monthly frequency of transactions
           - Total monthly spending in the category
           - Typical household spending patterns
           - Add 10-20% buffer for flexibility
        
        4. Examples of good budget suggestions:
           - Coffee & Snacks: $25 (small regular expense)
           - Groceries: $400 (medium regular expense)
           - Rent: $1200 (large fixed expense)
           - Entertainment: $150 (medium variable expense)

        Important Guidelines:
        - ALWAYS suggest budgets as whole numbers (no decimals)
        - Make suggestions slightly higher than current spending to allow flexibility
        - Consider both transaction frequency and total amounts
        - Use common sense for different expense types

        Transactions to analyze:
        {json.dumps(transaction_list, indent=2)}

        Return the response in this exact JSON format:
        {{
            "categories": {{
                "category_name": {{
                    "transactions": [
                        {{
                            "name": "transaction_name",
                            "amount": amount,
                            "date": "date"
                        }}
                    ],
                    "suggested_budget": rounded_monthly_budget_amount,
                    "description": "Brief description of what this category includes and why this budget is suggested"
                }}
            }}
        }}
        """

        # Get categorization from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial expert who understands practical budgeting. Always suggest realistic, rounded budget numbers that make sense for each category."},
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the response
        try:
            categorized_data = json.loads(response.choices[0].message.content)
            
            # Validate the categorization and budget suggestions
            all_transactions = set(tx["name"] for tx in transaction_list)
            categorized_transactions = set()
            
            # Validate and round budget suggestions
            for category, data in categorized_data["categories"].items():
                if isinstance(data, dict):
                    if "transactions" in data:
                        categorized_transactions.update(tx["name"] for tx in data["transactions"])
                    
                    # Ensure budget is a whole number
                    if "suggested_budget" in data:
                        data["suggested_budget"] = round(float(data["suggested_budget"]))
            
            # Check for missing transactions
            missing_transactions = all_transactions - categorized_transactions
            if missing_transactions:
                st.warning(f"Some transactions were not categorized: {', '.join(missing_transactions)}")
                
            return categorized_data["categories"]
        except json.JSONDecodeError:
            st.error("Failed to parse AI response. Please try again.")
            return {}

    except Exception as e:
        st.error(f"Error categorizing transactions: {str(e)}")
        return {}

def analyze_transactions_for_budgets(categorized_transactions):
    """Analyze categorized transactions to suggest appropriate budgets using OpenAI."""
    try:
        # Prepare prompt for OpenAI
        prompt = f"""Based on the following categorized spending patterns, suggest appropriate monthly budgets for each category.
        Consider that these are actual spending amounts and suggest reasonable budgets that allow for some flexibility.
        
        Categorized Spending Analysis:
        {json.dumps(categorized_transactions, indent=2)}
        
        Please suggest budgets in the format:
        Category: Suggested Budget
        """
        
        # Get OpenAI API key
        api_key = Config.get_openai_api_key()
        openai.api_key = api_key
        
        # Get budget suggestions
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial advisor helping set reasonable monthly budgets."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response
        suggestions = {}
        for line in response.choices[0].message.content.split('\n'):
            if ':' in line:
                category, budget = line.split(':')
                try:
                    budget = float(budget.strip().replace('$', ''))
                    suggestions[category.strip()] = budget
                except ValueError:
                    continue
        
        return suggestions
    
    except Exception as e:
        st.error(f"Error getting budget suggestions: {str(e)}")
        return {}

def show_budget_tracker():
    st.title("📊 Budget Tracker - Monthly Overspending")

    # Add Account Selector at the top
    selected_accounts = show_account_selector()

    if not selected_accounts:
        st.warning("⚠️ Please select at least one account to view budget tracking.")
        st.stop()

    # Ensure transactions exist
    if 'transactions' not in st.session_state:
        st.warning("⚠️ Please fetch transactions from the Home page first.")
        st.stop()

    # Filter transactions for selected accounts
    transactions = [
        tx for tx in st.session_state['transactions']
        if tx.get('account_id') in selected_accounts
    ]

    if not transactions:
        st.warning("No transactions found for selected accounts.")
        st.stop()

    # Initialize or reuse BudgetTracker
    if 'budget_tracker' not in st.session_state:
        st.session_state['budget_tracker'] = BudgetTracker()
    budget_tracker = st.session_state['budget_tracker']

    # Initialize categorized transactions in session state if not exists
    if 'categorized_transactions' not in st.session_state:
        st.session_state['categorized_transactions'] = {}

    # Extract available months from transactions
    all_months = sorted(set(
        date_parser.parse(tx['date']).strftime("%Y-%m") for tx in transactions
    ))
    
    # Add month selection with change detection
    if 'previous_month' not in st.session_state:
        st.session_state['previous_month'] = None
        
    selected_month = st.selectbox("📅 Select Month", all_months, index=len(all_months) - 1, key='month_selector')
    
    # Detect month change
    month_changed = selected_month != st.session_state['previous_month']
    st.session_state['previous_month'] = selected_month

    # Filter transactions for selected month
    filtered_tx = [
        tx for tx in transactions
        if date_parser.parse(tx['date']).strftime("%Y-%m") == selected_month
    ]

    # Categorize transactions if not already done for this month
    if selected_month not in st.session_state['categorized_transactions'] or month_changed:
        with st.spinner("🤖 AI is categorizing your transactions..."):
            categorized = categorize_transactions(filtered_tx)
            st.session_state['categorized_transactions'][selected_month] = categorized
            
            # Set initial budget limits from AI suggestions
            for category, data in categorized.items():
                if isinstance(data, dict) and 'suggested_budget' in data:
                    budget_tracker.set_monthly_limit(selected_month, category, data['suggested_budget'])
                    # Store in session state for the input fields
                    st.session_state[f"{selected_month}_{category}"] = data['suggested_budget']
            
            st.success("✅ Transactions categorized and budget suggestions applied!")
            
            # Automatically analyze spending when month changes
            budget_tracker.reset_month(selected_month)
            categorized_data = st.session_state['categorized_transactions'][selected_month]
            
            for category, data in categorized_data.items():
                if isinstance(data, dict) and 'transactions' in data:
                    total_spent = sum(tx['amount'] for tx in data['transactions'])
                    budget_tracker.monthly_expenses[selected_month][category] = total_spent

            overspending = budget_tracker.get_overspending_summary(selected_month)
            summary = budget_tracker.get_monthly_summary(selected_month)

            # Store chart data in session_state
            st.session_state['chart_summary'] = summary
            st.session_state['chart_month'] = selected_month

    # Show charts if data exists
    if 'chart_summary' in st.session_state and 'chart_month' in st.session_state:
        summary = st.session_state['chart_summary']
        selected_month = st.session_state['chart_month']

        # Convert summary to DataFrame for Altair
        df = pd.DataFrame(summary)
        df['overspent'] = df['spent'] > df['limit']
        df['remaining'] = df['limit'] - df['spent']
        df['remaining'] = df['remaining'].clip(lower=0)
        df['percentage_spent'] = (df['spent'] / df['limit'] * 100).round(1)

        # Prepare data for side-by-side bars
        chart_data = []
        for _, row in df.iterrows():
            # Add budget bar data
            chart_data.append({
                'category': row['category'],
                'type': 'Budget',
                'amount': row['limit'],
                'spent': row['spent'],
                'remaining': row['remaining'],
                'percentage': row['percentage_spent'],
                'overspent': row['overspent'],
                'color_type': 'Budget'  # Add color type for budget bars
            })
            # Add spent bar data
            chart_data.append({
                'category': row['category'],
                'type': 'Spent',
                'amount': row['spent'],
                'spent': row['spent'],
                'remaining': row['remaining'],
                'percentage': row['percentage_spent'],
                'overspent': row['overspent'],
                'color_type': 'Overspent' if row['overspent'] else 'Spent'  # Add color type for spent bars
            })

        # Convert to DataFrame
        chart_df = pd.DataFrame(chart_data)

        # Create a selection for highlighting
        highlight = alt.selection_single(
            on='mouseover',
            fields=['category'],
            nearest=True
        )

        # Create the chart
        chart = alt.Chart(chart_df).mark_bar().encode(
            x=alt.X('category:N', 
                title=None,
                sort=alt.SortField(field='amount', order='descending'),
                axis=alt.Axis(
                    labelAngle=-45,
                    labelAlign='right',
                    labelPadding=4
                )
            ),
            y=alt.Y('amount:Q', 
                title='Amount ($)',
                axis=alt.Axis(grid=True)
            ),
            xOffset=alt.XOffset(
                "type:N",
                title=None
            ),
            color=alt.Color(
                'color_type:N',
                scale=alt.Scale(
                    domain=['Budget', 'Spent', 'Overspent'],
                    range=['#94A3B8', '#3B82F6', '#EF4444']
                ),
                legend=alt.Legend(
                    orient='top',
                    title=None,
                    labelFontSize=12
                )
            ),
            opacity=alt.condition(highlight, alt.value(1), alt.value(0.9)),
            tooltip=[
                alt.Tooltip('category:N', title='Category'),
                alt.Tooltip('type:N', title='Type'),
                alt.Tooltip('amount:Q', title='Amount', format='$,.2f'),
                alt.Tooltip('remaining:Q', title='Remaining', format='$,.2f'),
                alt.Tooltip('percentage:Q', title='% of Budget Used', format='.1f')
            ]
        ).properties(
            width=700,
            height=400
        ).add_selection(
            highlight
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            labelFontSize=12,
            titleFontSize=14,
            gridColor='#f0f0f0',
            domainColor='#ddd'
        )

        # Add chart title and description
        st.subheader("Budget vs. Spending")
        st.caption("Compare your budgeted amounts with actual spending")
        
        # Display the chart
        st.altair_chart(chart, use_container_width=True)

        # Detailed Summary Table
        st.subheader("📋 Detailed Summary")
        summary_df = pd.DataFrame(summary)
        summary_df['Status'] = summary_df.apply(
            lambda row: '⚠️ Overspent' if row['spent'] > row['limit'] else '✅ Within Budget',
            axis=1
        )
        summary_df['Remaining'] = (summary_df['limit'] - summary_df['spent']).clip(lower=0)
        st.dataframe(
            summary_df[['category', 'spent', 'limit', 'Remaining', 'Status']],
            use_container_width=True
        )

    # Budget Settings Section
    st.subheader("💰 Budget Settings")
    
    # Get categories from AI categorization
    if selected_month in st.session_state['categorized_transactions']:
        categories = list(st.session_state['categorized_transactions'][selected_month].keys())
    else:
        categories = []
    
    # Add AI Budget Suggestions
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🤖 Get AI Budget Suggestions"):
            with st.spinner("Analyzing spending patterns..."):
                categorized = categorize_transactions(filtered_tx)
                if categorized:
                    for category, data in categorized.items():
                        if 'suggested_budget' in data:
                            key = f"{selected_month}_{category}"
                            st.session_state[key] = data['suggested_budget']
                            budget_tracker.set_monthly_limit(selected_month, category, data['suggested_budget'])
                    st.success("✅ Budget suggestions updated!")
                else:
                    st.warning("No suggestions available for this month's data.")

    # Show budget input fields
    for category in categories:
        key = f"{selected_month}_{category}"
        if key not in st.session_state:
            # Get suggested budget from categorized data
            if selected_month in st.session_state['categorized_transactions']:
                category_data = st.session_state['categorized_transactions'][selected_month].get(category)
                if isinstance(category_data, dict):
                    suggested_budget = category_data.get('suggested_budget', 0.0)
                else:
                    suggested_budget = 0.0
            else:
                suggested_budget = 0.0
            st.session_state[key] = suggested_budget
        
        # Show the input field with the current/suggested value
        limit = st.number_input(
            f"{category} Limit ($)",
            min_value=0.0,
            step=10.0,
            key=key,
            help=f"Set your monthly budget limit for {category}"
        )
        budget_tracker.set_monthly_limit(selected_month, category, limit)

    # Analyze Spending button
    if st.button("📈 Analyze Spending") or month_changed:
        # Track expenses using AI-categorized transactions
        budget_tracker.reset_month(selected_month)
        categorized_data = st.session_state['categorized_transactions'][selected_month]
        
        for category, data in categorized_data.items():
            if isinstance(data, dict) and 'transactions' in data:
                total_spent = sum(tx['amount'] for tx in data['transactions'])
                budget_tracker.monthly_expenses[selected_month][category] = total_spent

        overspending = budget_tracker.get_overspending_summary(selected_month)
        summary = budget_tracker.get_monthly_summary(selected_month)

        # Store chart data in session_state
        st.session_state['chart_summary'] = summary
        st.session_state['chart_month'] = selected_month

        # Add notifications
        if overspending:
            if 'notifications' not in st.session_state:
                st.session_state['notifications'] = []
            new_notes = generate_notifications(overspending, selected_month)
            st.session_state['notifications'].extend(new_notes)

        if not month_changed:  # Only rerun if button was clicked, not if month changed
            st.rerun()

    # Check if we need to rerun due to account selection change
    if st.session_state.get('account_selection_changed', False):
        st.session_state.account_selection_changed = False
        st.rerun()
