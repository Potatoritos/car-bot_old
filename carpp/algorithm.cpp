#include <algorithm>
#include <array>
#include <queue>
#include <string>
#include <utility>
#include <vector>

#define INF 0x3f3f3f3f

namespace carpp::algorithm {

int levenshtein(const std::string& s1, const std::string& s2,
        int w_del/* = 1*/, int w_ins/* = 1*/, int w_sub/* = 1*/) {

    //int dp[2][s2.size()+1];
    std::vector<int> dp[2] = {std::vector<int>(s2.size()+1), std::vector<int>(s2.size()+1)};
    //
    //std::array<std::array<int, s2.size()+1>, 2> dp;
    bool row = 0;

    for (size_t i = 0; i <= s2.size(); i++) {
        dp[0][i] = i * w_ins;
    }
    for (size_t i = 1; i <= s1.size(); i++) {
        row = !row;
        dp[row][0] = i * w_del;

        for (size_t j = 1; j <= s2.size(); j++) {
            if (s1[i-1] == s2[j-1]) {
                dp[row][j] = dp[!row][j-1];
            } else {
                dp[row][j] = std::min({
                    w_del + dp[!row][j],
                    w_ins + dp[row][j-1],
                    w_sub + dp[!row][j-1]
                });
            }
        }
    }

    return dp[row][s2.size()];
}

int func_levenshtein(const std::string& s1, const std::string& s2,
        int w_del, int w_ins, int w_sub) {

    return levenshtein(s1, s2, w_del, w_ins, w_sub);
}

std::vector<std::pair<int, int>> func_fuzzy_match(
        const std::string& query, const std::vector<std::string>& against, size_t amount) {

    std::priority_queue<std::pair<int, int>> best_matches;

    amount = std::min(amount, against.size());

    for (size_t i = 0; i < against.size(); i++) {
        int dist = levenshtein(query, against[i], 9, 1, 10);
        best_matches.push({dist, i});
        if (best_matches.size() > amount) best_matches.pop();
    }

    std::vector<std::pair<int, int>> res;
    res.reserve(best_matches.size());

    while (!best_matches.empty()) {
        res.push_back(best_matches.top());
        best_matches.pop();
    }

    return res;
}

std::pair<int, int> func_fuzzy_match_one(
        const std::string& query, const std::vector<std::string>& against) {

    int min_dist=INF, idx=-1;

    for (size_t i = 0; i < against.size(); i++) {
        int dist = levenshtein(query, against[i], 9, 1, 10);
        if (dist < min_dist) {
            min_dist = dist;
            idx = i;
        }
    }

    return {min_dist, idx};
}

}

