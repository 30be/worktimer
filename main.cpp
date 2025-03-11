#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <thread>
using namespace std;

enum class state : int { BIG_REST, SMALL_REST, WORK, NOTHING };
enum class action : int { WRITE_DONE, WRITE_SKIPPED, DISMISS, DISABLE };

const auto HOME_PATH = filesystem::path(getenv("HOME"));
const auto MESSAGE_FILE = HOME_PATH / "msg";
const auto SOUNDS_PATH = HOME_PATH / ".local/share/sounds/worktimer";
const array<string, 4> states = {"Big rest", "Small rest", "Work", "Nothing yet"};
const array<string, 5> actions = {"Done", "Skipped", "Okay", "Disable"};

static bool run_flag = true;

string make_param(action action) { return format(" --action={0}={0} ", actions[(int)action]); }
auto GetHM() {
    time_t now_c = chrono::system_clock::to_time_t(chrono::system_clock::now());
    tm *local_time = localtime(&now_c);
    return tuple{local_time->tm_hour, local_time->tm_min, local_time->tm_sec};
}
constexpr string trim(string s, const char *t = " \t\n\r\f\v") {
    s.erase(0, s.find_first_not_of(t));
    s.erase(s.find_last_not_of(t) + 1);
    return s;
}
optional<string> exec(const string &cmd) {
    array<char, 128> buffer;
    string result;
    cout << "Executing: " << quoted(cmd) << endl;
    auto pipe = unique_ptr<FILE, decltype(&pclose)>(popen(cmd.data(), "r"), pclose);
    if (!pipe)
        return nullopt;
    while (fgets(buffer.data(), static_cast<int>(buffer.size()), pipe.get()))
        result += buffer.data();
    return trim(result);
}
void take_photo(auto name) {
    exec(format("fswebcam -b --no-banner ~/Pictures/worktimer/{}.jpg", name));
}
// Sorry for this
string predict_place() {
    ifstream file(HOME_PATH / ".worklog");
    string last_line;
    string current_line;

    while (getline(file, current_line))
        last_line = current_line;
    return last_line.find("HM") ? "HM" : "CW";
}
void store_score() { ofstream(HOME_PATH / ".worklog", ios_base::app) << "depth: 0/9\n"; }
void store_workunit(bool success, auto time, chrono::minutes duration = 25min) {
    time_t start = chrono::system_clock::to_time_t(time - duration);
    time_t end = chrono::system_clock::to_time_t(time);

    ofstream(HOME_PATH / ".worklog", ios_base::app)
        << put_time(localtime(&start), "%Y-%m-%d") << put_time(localtime(&start), " %H:%M-")
        << put_time(localtime(&end), "%H:%M")
        << format(" [{}] {} \n", success ? "x" : " ", predict_place());
}

string read_and_remove(const string &file) {
    ifstream input(file);
    if (!input)
        return "";
    string res = "Msg: " + string((istreambuf_iterator<char>(input)), istreambuf_iterator<char>());
    filesystem::remove(file);
    return res;
}
string get_actions(state new_state) {
    return int(new_state) < 2 ? make_param(action::WRITE_DONE) + make_param(action::WRITE_SKIPPED)
                              : make_param(action::DISMISS);
}
void handle_transition(state old_state, state new_state) {
    array<string, 3> sounds = {".click.ogg", "click.ogg", "string.ogg"};
    auto [h, m, s] = GetHM();
    auto event_time = chrono::system_clock::now();
    time_t end_time = chrono::system_clock::to_time_t(event_time);
    auto message = format("{:02}:{:02} {} finished. {}. {}", h, m, states[((int)old_state + 4) % 4],
                          states[(int)new_state], read_and_remove(MESSAGE_FILE));
    auto sound_path = (SOUNDS_PATH / sounds[(int)new_state]).string();
    auto photo_path = (ostringstream() << put_time(localtime(&end_time), "%Y-%m-%d_%H:%M")).str();
    auto cmd = format("notify-send {} -a worktimer -u critical -e -t 10000 \"{}\"",
                      get_actions(new_state) + make_param(action::DISABLE), message);

    take_photo(photo_path);
    exec("paplay " + sound_path);
    auto res = exec(cmd);

    if (res and old_state == state::WORK) {
        if (res.value() == actions[(int)action::DISABLE]) {
            run_flag = false;
            return;
        }
        store_workunit(res.value() == actions[(int)action::WRITE_DONE], event_time);
        if (new_state == state::BIG_REST)
            store_score();
        exec("alacritty -e nvim -c 'normal! GA' ~/.worklog");
    }
}
int main() {
    using enum state;
    state current_state = NOTHING, newstate = NOTHING;
    while (run_flag) {
        auto [h, m, s] = GetHM();
        newstate = (h % 3 == 0 && m < 35) ? BIG_REST : (m % 30 < 5) ? SMALL_REST : WORK;
        // current_state = WORK;
        // newstate = SMALL_REST;
        if (current_state != newstate)
            thread(handle_transition, current_state, newstate).detach();
        current_state = newstate;
        this_thread::sleep_for(chrono::seconds(1));
    }
}
