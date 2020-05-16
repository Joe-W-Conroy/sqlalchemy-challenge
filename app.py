import numpy as np
import sqlalchemy
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to the tables
measurements_table = Base.classes.measurement
stations_table = Base.classes.station

# Flask Setup
app = Flask(__name__)

# Flask Routes
@app.route("/")
def home():
    """This is the Home Page!"""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date(/end_date)"
    )

@app.route("/api/v1.0/precipitation")
def getprecip():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all precipitation data
    results = session.query(measurements_table.date, measurements_table.prcp).all()

    # Close the session
    session.close()

    # Convert list of tuple pairs into a dict
    precip_list = {}

    for tup in results:
        try:
            precip_list[tup[0]].append(tup[1])
        except KeyError:
            precip_list[tup[0]] = [tup[1]]

    return jsonify(precip_list)

@app.route("/api/v1.0/stations")
def getstations():
    session = Session(engine)
    results = session.query(stations_table.station).all()
    session.close()
    stations_list = list(np.ravel(results))

    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def gettobs():
    first_year = '0000-00-00'

    session = Session(engine)

    # Get the most active station
    most_active_station = session.query(measurements_table.station, func.count()).\
    group_by(measurements_table.station).order_by(-func.count()).first()[0]

    # Now use it to find the first acceptable date
    for row in session.query(measurements_table).filter(measurements_table.station == most_active_station):
        if (first_year < row.date):
            first_year = row.date

    first_year = dt.datetime.strptime(first_year, '%Y-%m-%d')
    first_year = first_year.replace(year=first_year.year - 1)

    # Now grab all the tobs data for the most active station, starting at 1 year before its'
    # last recorded data (told to query the dates and temperatures)
    results = session.query(measurements_table.date, measurements_table.tobs).\
    filter(measurements_table.date >= first_year.strftime('%Y-%m-%d')).\
    filter(measurements_table.station == most_active_station).\
    group_by(measurements_table.date).all()

    session.close()

    # Now organize and return the data (temperatures only)
    tobs_list = []

    for tup in results:
        tobs_list.append(tup[1])

    return jsonify(tobs_list)

@app.route("/api/v1.0/<start_date>/<end_date>")
def interval(start_date, end_date):
    try:
        # Set the dates for the filtering
        date1 = dt.datetime.strptime(start_date, '%Y-%m-%d')
        date2 = dt.datetime.strptime(end_date, '%Y-%m-%d')

        if (date1 > date2):
            return(f"Please enter the earlier date ({end_date}) ahead of the later date ({start_date}).")
        else:
            # Run the session
            session = Session(engine)
            results = session.query(
                func.min(measurements_table.tobs),
                func.avg(measurements_table.tobs),
                func.max(measurements_table.tobs)
            ).filter(measurements_table.date >= date1.strftime('%Y-%m-%d')).\
            filter(measurements_table.date <= date2.strftime('%Y-%m-%d')).all()

            session.close()

            # Now organize and return
            summaryinfo = list(np.ravel(results))

            return jsonify(summaryinfo)
    except ValueError:
        return(f"Either the start ({start_date}) or stop ({end_date}) dates do not match the format 'YYYY-MM-DD'")

@app.route("/api/v1.0/<date_entered>")
def from_start(date_entered):
    try:
        # Set the date for the filtering
        date = dt.datetime.strptime(date_entered, '%Y-%m-%d')

        # Run the session
        session = Session(engine)

        results = session.query(
            func.min(measurements_table.tobs),
            func.avg(measurements_table.tobs),
            func.max(measurements_table.tobs)
        ).filter(measurements_table.date >= date.strftime('%Y-%m-%d')).all()

        session.close()

        # Now organize and return
        summaryinfo = list(np.ravel(results))

        return jsonify(summaryinfo)
    except ValueError:
        return(f"The entered date ({date_entered}) does not match the format 'YYYY-MM-DD'")

# Main starts here
if __name__ == '__main__':
    app.run(debug=True)