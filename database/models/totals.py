from sqlalchemy import Column, types

from database.models.base import Base


class Totals(Base):
    __tablename__ = "totals"
    id = Column("id", types.Integer, primary_key=True)

    label_analysis_success_count = Column(types.Integer)
    label_analysis_failure_count = Column(types.Integer)
    label_analysis_mean_duration = Column(types.Float)
    label_analysis_median_duration = Column(types.Float)
    label_analysis_p90_duration = Column(types.Float)
    label_analysis_stdev_duration = Column(types.Float)

    regular_tests_success_count = Column(types.Integer)
    regular_tests_failure_count = Column(types.Integer)
    regular_tests_mean_duration = Column(types.Float)
    regular_tests_median_duration = Column(types.Float)
    regular_tests_p90_duration = Column(types.Float)
    regular_tests_stdev_duration = Column(types.Float)

    def __repr__(self):
        return (
            f"-> Label Analysis\n"
            + f"\tSuccess: {self.label_analysis_success_count}; Failed: {self.label_analysis_failure_count}\n"
            + f"\tMean: {self.label_analysis_mean_duration}s (stdev {self.label_analysis_stdev_duration}s)\n"
            + f"\Meadian: {self.label_analysis_median_duration}s\n"
            + f"\p90: {self.label_analysis_p90_duration}s\n"
            + f"-> Regular tests\n"
            + f"\tSuccess: {self.regular_tests_success_count}; Failed: {self.regular_tests_failure_count}\n"
            + f"\tMean: {self.regular_tests_mean_duration}s (stdev {self.regular_tests_stdev_duration}s)\n"
            + f"\Meadian: {self.regular_tests_median_duration}s\n"
            + f"\p90: {self.regular_tests_p90_duration}s\n"
        )
