#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <thread>
using namespace std;
bool run_flag = true;
auto GetHM() {
    time_t now_c = chrono::system_clock::to_time_t(chrono::system_clock::now());
    tm *local_time = localtime(&now_c);
    return tuple{local_time->tm_hour, local_time->tm_min, local_time->tm_sec};
}
optional<string> exec(const string &cmd) {
    cout << "Executing: " << quoted(cmd) << endl;
    array<char, 128> buffer;
    string result;
    unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.data(), "r"), pclose);
    if (!pipe)
        return nullopt;
    while (fgets(buffer.data(), static_cast<int>(buffer.size()), pipe.get()))
        result += buffer.data();
    return result;
}
auto cur_time() {
    time_t now_c = chrono::system_clock::to_time_t(chrono::system_clock::now());
    tm *local_time = localtime(&now_c);
    return put_time(local_time, "%Y-%m-%d %H:%M");
}
void store_action(string action, auto time) {
    using namespace chrono;
    cout << "Action: " << quoted(action) << endl;
    static mutex action_mutex;
    lock_guard guard(action_mutex);

    if (action == "Disable")
        run_flag = false;
    else if (action != "Okay")
        ofstream(filesystem::path(getenv("HOME")) / ".worklog", ios_base::app)
            << time << format(" {:<8}\n", action);
}

constexpr string trim(string s, const char *t = " \t\n\r\f\v") {
    s.erase(0, s.find_first_not_of(t));
    s.erase(s.find_last_not_of(t) + 1);
    return s;
}
void handle_event(int state, int newstate) {
    array<string, 3> messages = {"Big rest", "Small rest", "Work"};
    array<string, 3> sounds = {".click.ogg", "click.ogg", "string.ogg"};
    string actions = newstate == 2 or state == -1 ? "--action=Okay=Okay"
                                                  : "--action=Done=Done --action=Skipped=Skipped";
    auto t = cur_time();
    auto [h, m, s] = GetHM();

    exec(format("paplay {}", (filesystem::current_path() / sounds[newstate]).string()));
    auto res = exec(format("notify-send {} --action=Disable=Disable -a worktimer -u "
                           "critical -e -t 10000 \"{:02}:{:02} {} finished. {}\"",
                           actions, h, m, messages[state], messages[newstate]));
    if (res) {
        store_action(trim(std::move(res.value())), t);
        if (state == 2 and res.value() != "Disable")
            exec("alacritty -e nvim -c 'normal! GA' ~/.worklog");
    } else
        cout << "Something went wrong\n";
}
int main() {
    int state = -1, newstate = -1;
    while (run_flag) {
        auto [h, m, s] = GetHM();
        newstate = (h % 3 == 0 && m < 35) ? 0 : (m % 30 < 5) ? 1 : 2;
        // newstate = 1;
        // state = 2;
        if (state != newstate)
            thread(handle_event, state, newstate).detach();
        state = newstate;
        this_thread::sleep_for(chrono::seconds(1));
    }
}
