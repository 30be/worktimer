#include <chrono>
#include <iostream>
#include <thread>
using namespace std;
auto GetHM() {
    time_t now_c = chrono::system_clock::to_time_t(chrono::system_clock::now());
    tm *local_time = localtime(&now_c);
    return tuple{local_time->tm_hour, local_time->tm_min, local_time->tm_sec};
}

int main() {
    int state = -1, newstate = -1;
    while (true) {
        auto [h, m, s] = GetHM();
        array<string, 3> messages = {"Big rest", "Small rest", "Work"};
        if (h % 3 == 0 && m < 35)
            newstate = 0;
        else if (m % 30 < 5)
            newstate = 1;
        else
            newstate = 2;
        array<string, 3> sounds = {"/usr/share/sounds/gnome/default/alerts/click.ogg",
                                   "usr/share/sounds/gnome/default/alerts/click.ogg",
                                   "/usr/share/sounds/gnome/default/alerts/string.ogg"};
        auto msg = format("notify-send -a worktimer -u normal -e -t 10000 \"{}\" && paplay {}",
                          messages[newstate], sounds[newstate]);
        if (state != newstate)
            system(msg.c_str());
        state = newstate;
        cout << format("{} time: {:02}:{:02}:{:02}\n", messages[state], h, m, s);
        this_thread::sleep_for(chrono::seconds(1));
    }
}
