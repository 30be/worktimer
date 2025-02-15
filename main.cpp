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
void store_action(bool success, auto time) {
    time_t start = chrono::system_clock::to_time_t(time - 25min);
    time_t end = chrono::system_clock::to_time_t(time);
    static mutex action_mutex;
    lock_guard guard(action_mutex);

    ofstream(filesystem::path(getenv("HOME")) / ".worklog", ios_base::app)
        << put_time(localtime(&start), "%Y-%m-%d") << put_time(localtime(&start), " %H:%M-")
        << put_time(localtime(&end), "%H:%M") << format(" [{}] CW \n", success ? "x" : " ");
}
bool handle_action(auto action, auto time) {
    cout << "Action: " << quoted(action) << endl;
    if (action == "Done")
        store_action(true, time);
    else if (action == "Skipped" or action == "")
        store_action(false, time);
    else if (action == "Disable")
        return run_flag = false;
    else if (action == "Okay")
        return false;

    return true;
}

constexpr string trim(string s, const char *t = " \t\n\r\f\v") {
    s.erase(0, s.find_first_not_of(t));
    s.erase(s.find_last_not_of(t) + 1);
    return s;
}
void handle_event(int state, int newstate) {
    array<string, 4> messages = {"Big rest", "Small rest", "Work", "Nothing yet"};
    array<string, 3> sounds = {".click.ogg", "click.ogg", "string.ogg"};
    string actions = newstate == 2 or state == -1 ? "--action=Okay=Okay"
                                                  : "--action=Done=Done --action=Skipped=Skipped";
    auto [h, m, s] = GetHM();
    auto event_time = std::chrono::system_clock::now();
    exec(format("paplay {}", (filesystem::current_path() / sounds[newstate]).string()));
    auto res = exec(format("notify-send {} --action=Disable=Disable -a worktimer -u "
                           "critical -e -t 10000 \"{:02}:{:02} {} finished. {}\"",
                           actions, h, m, messages[(state + 4) % 4], messages[newstate]));
    if (res and handle_action(trim(std::move(res.value())), event_time))
        exec("alacritty -e nvim -c 'normal! GA' ~/.worklog");
    else
        cout << "Something went wrong\n";
}
int main() {
    int state = -1, newstate = -1;
    while (run_flag) {
        auto [h, m, s] = GetHM();
        newstate = (h % 3 == 0 && m < 35) ? 0 : (m % 30 < 5) ? 1 : 2;
        newstate = 1;
        state = 2;
        if (state != newstate)
            thread(handle_event, state, newstate).detach();
        state = newstate;
        this_thread::sleep_for(chrono::seconds(1));
    }
}
