#pragma once

#include <string>
#include <vector>
#include <utility>

namespace carpp::algorithm {

int levenshtein(const std::string& s1, const std::string& s2,
        int w_del=1, int w_ins=1, int w_sub=1);

int func_levenshtein(const std::string& s1, const std::string& s2,
        int w_del, int w_ins, int w_sub);

std::vector<std::pair<int, int>> func_fuzzy_match(
        const std::string& query, const std::vector<std::string>& against, size_t amount);

std::pair<int, int> func_fuzzy_match_one(
        const std::string& query, const std::vector<std::string>& against);

}
