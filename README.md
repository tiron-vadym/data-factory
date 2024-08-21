# FastAPI Project

This project uses FastAPI to create a RESTful API integrated with SQLAlchemy for managing a MySQL database. It includes functionality for managing credits, plans, payments, and other related entities.


## Installation

- Install MySQL and create db
- To set up the project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tiron-vadym/data-factory
   cd data_API
   python -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   set SQLALCHEMY_DATABASE_URL=<set database url>
   alembic upgrade head
   uvicorn main:app --reload
   

## Overview

The project provides the following API endpoints:

- `/user_credits/{user_id}`: Retrieve credit information for a user.
- `/plans_insert`: Insert new plans from a file.
- `/plans_performance`: Get information about plan performance.
- `/year_performance`: Retrieve summarized information for a specified year.
