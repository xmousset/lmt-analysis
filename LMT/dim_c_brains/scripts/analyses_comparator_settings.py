# """
# @author: xmousset
# """

# from typing import Any
# from pathlib import Path

# import pandas as pd

# from dim_c_brains.scripts.parameter_saver import ParameterSaver


# class AnalysesComparatorSettings:
#     """Manage settings for LMT database analyzer.

#     Parameters
#     ----------
#     comparator: str
#         The type of comparison to perform between analyses. Default is "RFID".
#     night_begin: int
#         Hour when the night begins (0-23). Defaults to 20 (8 *p.m.*).
#     night_duration: int
#         Duration of the night in hours. Defaults to 12 (12 hours so from
#         8 *p.m.* to 8 *a.m.* for example).
#     output_folder: Path | None
#         The folder where the comparison results will be saved. If None, it will
#         be saved next to the first listed analysis, with a name based on the
#         comparator type. Default is None.

#     To add another parameter, simply add it in both the `get_default_settings`
#     and the `reset` methods of the class, all other methods will automatically
#     handle it.
#     """

#     MAIN_TABLE = "main_complete_table_Download_data.xlsx"

#     @staticmethod
#     def get_default_settings() -> dict[str, Any]:
#         """Get the default settings values as a dictionary."""
#         default_settings = {
#             "night_begin": 20,
#             "night_duration": 12,
#             "output_folder": None,
#             "report_color": "RFID",
#             "report_x_axis": "START_TIME",
#         }
#         return default_settings

#     @classmethod
#     def get_all_keys(cls):
#         """Get all settings names."""
#         return [key for key in cls.get_default_settings()]

#     @staticmethod
#     def convert_in_str(initial_dict: dict[str, Any]) -> dict[str, Any]:
#         """Convert the dict settings values in string."""
#         new_dict = initial_dict.copy()

#         if new_dict["output_folder"] is not None:
#             new_dict["output_folder"] = str(new_dict["output_folder"])

#         return new_dict

#     @staticmethod
#     def convert_from_str(initial_dict: dict[str, Any]) -> dict[str, Any]:
#         """Convert the dict settings values from string to the correct type."""
#         new_dict = initial_dict.copy()

#         if new_dict["output_folder"] is not None:
#             new_dict["output_folder"] = Path(new_dict["output_folder"])

#         return new_dict

#     @classmethod
#     def get_common_columns_from_list(cls, path_list: list[Path]) -> list[str]:
#         """Get common columns in all analyses."""
#         common_columns: set[str] = set()
#         for path in path_list:
#             df = pd.read_excel(path / cls.MAIN_TABLE)
#             if not common_columns:
#                 common_columns = set(df.columns)
#             else:
#                 common_columns = common_columns.intersection(set(df.columns))
#         if "Unnamed: 0" in common_columns:
#             common_columns.remove("Unnamed: 0")
#         if "ID" in common_columns:
#             common_columns.remove("ID")
#         return sorted(common_columns)

#     def __init__(self, analyses_path: list[Path]):
#         """Initialize the settings with default values."""
#         self.analyses_path = analyses_path
#         self.reset()
#         self._saver = ParameterSaver()

#     def get_common_columns(self) -> list[str]:
#         """Get common columns in all analyses."""
#         return self.get_common_columns_from_list(self.analyses_path)

#     def reset(self):
#         """Reset the settings to their initial values."""

#         default_settings = AnalysesComparatorSettings.get_default_settings()

#         self.night_begin: int = default_settings["night_begin"]
#         self.night_duration: int = default_settings["night_duration"]
#         self.output_folder: Path | None = default_settings["output_folder"]
#         self.report_color: str = default_settings["report_color"]
#         self.report_x_axis: str = default_settings["report_x_axis"]

#     def as_dict(self) -> dict[str, Any]:
#         """Get the settings as a dictionary."""
#         settings = {}
#         for key in AnalysesComparatorSettings.get_all_keys():
#             settings[key] = getattr(self, key)
#         return settings

#     def as_str_dict(self):
#         """Get the settings as a dictionary without class or object values
#         (only int, float, bool, None and str). Useful for saving the settings
#         in a JSON file."""
#         return AnalysesComparatorSettings.convert_in_str(self.as_dict())

#     def update_from_dict(self, settings_dict: dict[str, Any]):
#         """Update the settings from a dictionary."""
#         update_dict = self.as_dict()
#         update_dict.update(settings_dict)

#         for key in AnalysesComparatorSettings.get_all_keys():
#             setattr(self, key, update_dict[key])

#     def save(self, file_path: Path):
#         """Save the settings to a JSON file."""

#         if self._saver is None:
#             raise ValueError(
#                 "No saver defined for LMT-EYE settings. Cannot save settings."
#             )

#         settings = self.as_str_dict()

#         self._saver.reset()
#         self._saver.set_values(settings)
#         if file_path:
#             self._saver.save(file_path)
#         else:
#             print("No file selected.")

#     def load(self, file_path: Path):
#         """Load the settings from a JSON file."""

#         if self._saver is None:
#             raise ValueError(
#                 "No saver defined for LMT-EYE settings. Cannot load settings."
#             )
#         self.reset()
#         self._saver.load(file_path)
#         settings = self._saver.get_parameters()
#         settings = AnalysesComparatorSettings.convert_from_str(settings)
#         self.update_from_dict(settings)

#     def as_html(self):
#         """Get the current settings as an HTML table."""
#         settings_str = self.as_str_dict()
#         settings = self.as_dict()
#         html = "<table border='1' cellpadding='4' cellspacing='0'>"
#         html += "<tr>"
#         html += "<th>Name</th>"
#         html += "<th>Type</th>"
#         html += "<th>JSON value</th>"
#         html += "</tr>"
#         for key in settings_str.keys():
#             str_value = settings_str[key]
#             type_value = type(settings[key]).__name__
#             html += "<tr>"
#             html += f"<td>{key}</td>"
#             html += f"<td>{type_value}</td>"
#             html += f"<td>{str_value}</td>"
#             html += "</tr>"
#         html += "</table>"
#         return html

#     def get_plot_parameters(self, df: pd.DataFrame) -> dict[str, Any]:
#         """Get the column name for *"color"* that are always used for the
#         reports plots.
#         Additionally, the unique values of the color column are sorted and
#         added in the "category_orders" parameter for better consistency of the
#         legends in the plots.

#         **Generic example**: *{"color": "RFID", "category_orders": {"RFID":
#         ["001", "002", "003"]}}*
#         """

#         if self.report_color not in df.columns:
#             raise ValueError(
#                 f"report_color '{self.report_color}' not found in dataframe."
#             )

#         plot_param = {
#             "color": self.report_color,
#             "category_orders": {
#                 self.report_color: sorted(df[self.report_color].unique())
#             },
#         }

#         return plot_param

#     def get_xlsx_parameters(self, df: pd.DataFrame) -> list[str]:
#         """Get the column names that are always used for the xlsx export.

#         **Generic example**: *["RFID", "START_TIME"]*
#         """

#         if self.report_color not in df.columns:
#             raise ValueError(
#                 f"report_color '{self.report_color}' not found in dataframe."
#             )

#         xlsx_param = ["RFID", self.report_x_axis]
#         if self.report_color != "RFID":
#             xlsx_param.append(self.report_color)

#         return xlsx_param
