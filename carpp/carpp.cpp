#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;

#include "algorithm.h"
#include "simulation.h"

PYBIND11_MODULE(carpp, m) {
    m.doc() = "Collection of functions to speed up carbot";

    m.def(
        "levenshtein",
        &carpp::algorithm::func_levenshtein,
        "Returns the levenshtein distance of two strings",
        py::arg("s1"),
        py::arg("s2"),
        py::arg("w_del") = 1,
        py::arg("w_ins") = 1,
        py::arg("w_sub") = 1
    );
    m.def(
        "fuzzy_match",
        &carpp::algorithm::func_fuzzy_match,
        "Returns (levenshtein dist., index)s of the most similar strings",
        py::arg("query"),
        py::arg("against"),
        py::arg("amount")
    );
    m.def(
        "fuzzy_match_one",
        &carpp::algorithm::func_fuzzy_match_one,
        "Returns (levenshtein dist., index) of the most similar string",
        py::arg("query"),
        py::arg("against")
    );
    m.def(
        "akpull",
        &carpp::simulation::func_akpull,
        "Simulates Arknights pulls",
        py::arg("trials"),
        py::arg("pulls"),
        py::arg("prob_rateup")
    );
}

