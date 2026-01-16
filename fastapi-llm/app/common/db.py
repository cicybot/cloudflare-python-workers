import os
import logging
from typing import Annotated, Union, List, Dict, Any, Tuple
from sqlalchemy import text
from fastapi import Depends, HTTPException
from sqlmodel import Session, SQLModel, create_engine
import traceback

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:200898@localhost:3307/llm")

if DATABASE_URL is not None:
    engine = create_engine(DATABASE_URL, echo=True)
else:
    db_dir = os.getenv("DB_DIR", ".")
    sqlite_file_name = f"{db_dir}/database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

# Dependency for getting the session
SessionDep = Annotated[Session, Depends(get_session)]


def execute_sql(
        query: str,
        params: Dict[str, Any] = None,
        session: Session = None  # Session will be passed explicitly from the route handler
):
    """
    Generic function to execute raw SQL queries for different operations.

    Args:
        query (str): The raw SQL query to be executed.
        params (dict): Parameters to be used in the query (optional).
        operation_type (str): Type of the SQL operation: 'select', 'insert', 'update', 'delete', 'create'.
        session (Session): The SQLAlchemy session passed explicitly from the route handler.

    Returns:
        - List of rows for SELECT queries.
        - Tuple containing:
            - Affected rows count (int).
            - Last inserted row ID (int) for INSERT, or `None` for other operations.
    """
    query = query.strip()
    operation_type = query[0:len("select")]
    params = params or {}
    logger.debug("select:%s ,sql:%s, params:%s",operation_type == "select" ,query,params)
    try:
        # Execute the query with parameters
        result = session.execute(text(query), params)

        if operation_type == "select":
            # Return the rows as a list of dicts for SELECT queries
            data = result.all()
            logger.debug("%s",data)
            return data
        else:
            # For INSERT, UPDATE, DELETE, CREATE, we commit the changes
            session.commit()
            affected_rows = result.rowcount  # Get the number of affected rows
            logger.debug("affected_rows:%s",affected_rows)
            if operation_type == "insert":
                # For INSERT, we also get the last inserted ID (if applicable)
                last_inserted_id = result.last_inserted_ids[0] if result.last_inserted_ids else None
                logger.debug(last_inserted_id,last_inserted_id)
                return affected_rows, last_inserted_id
            else:
                return affected_rows, None  # No ID returned for UPDATE, DELETE, or CREATE

    except Exception as e:
        logger.error("Error: %s",traceback.format_exc())
        session.rollback()  # Rollback if an error occurs
        raise HTTPException(status_code=500, detail=str(e))