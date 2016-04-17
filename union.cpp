// vim:set sw=4 et:

#include <set>
#include <cmath>
#include <queue>
#include <tuple>
#include <limits>
#include <vector>
#include <iostream>

#if 0
#define LOG(x) do { std::cout << "<!-- " << x << " -->" << std::endl; } while (0)
#define DEBUG_SCALE 5
#define DEBUG_BEGIN() do { \
    std::cout << "<?xml version=\"1.0\"?>\n" \
    << "<svg viewBox=\"0 0 100 100\" version=\"1.1\"" \
    << " xmlns=\"http://www.w3.org/2000/svg\">\n"; \
} while (0);
#define DEBUG_CIRCLE(x, y, r, color) do { \
    std::cout << "<circle cx=\"" << (DEBUG_SCALE * x) \
    << "\" cy=\"" << (DEBUG_SCALE * y) \
    << "\" r=\"" << (DEBUG_SCALE * r) \
    << "\" style=\"opacity:0.5;fill:" << color << "\"/>\n"; \
} while (0);
#define DEBUG_END() do { \
    std::cout << "</svg>\n"; \
} while (0);
#define DEBUG_LINE(x1, y1, x2, y2, w, color) do { \
    std::cout << "<line x1=\"" << (DEBUG_SCALE * x1) \
    << "\" y1=\"" << (DEBUG_SCALE * y1) \
    << "\" x2=\"" << (DEBUG_SCALE * x2) \
    << "\" y2=\"" << (DEBUG_SCALE * y2) \
    << "\" style=\"stroke-width:" << (DEBUG_SCALE * w) \
    << "px;stroke:" << color << "\"/>\n"; \
} while (0);
#else
#define LOG(x) do {} while (0)
#define DEBUG_BEGIN() do {} while (0)
#define DEBUG_CIRCLE(x, y, r, color) do {} while (0)
#define DEBUG_END() do {} while (0)
#define DEBUG_LINE(x1, y1, x2, y2, w, color) do {} while (0)
#endif

struct circle { size_t i; double x, y; };

std::ostream & operator<<(std::ostream & out, circle c) {
    return out << '(' << c.i << ':' << c.x << ',' << c.y << ')';
}

struct circle_by_greater_x {
    bool operator()(const circle & a, const circle & b) const {
        return a.x > b.x;
    }
};

struct circle_by_y {
    bool operator()(const circle & a, const circle & b) const {
        return std::tie(a.y, a.i) < std::tie(b.y, b.i);
    }
};

struct intersection {
    size_t i, j;
    double x, y;
};

std::ostream & operator<<(std::ostream & out, intersection o) {
    return out << '(' << (o.i == std::numeric_limits<size_t>::max() ? -1 : (int) o.i)
        << '/' << o.j << ':' << o.x << ',' << o.y << ')';
}

struct intersection_by_greater_x {
    bool operator()(const intersection & a, const intersection & b) const {
        return a.x > b.x;
    }
};

struct intersection_by_y {
    bool operator()(const intersection & a, const intersection & b) const {
        return std::tie(a.y, a.i, a.j) < std::tie(b.y, b.i, b.j);
    }
};

class boundary {
public:
    static constexpr double R = 0.5;
    static constexpr double twoR = 2 * R;
    static constexpr double R_sq = R * R;
    static constexpr double twoR_sq = 4 * R * R;

    void begin() {
        DEBUG_BEGIN();
        n_circle = 0;
    }

    void push(double x, double y) {
        circle c {n_circle++, x, y};
        double left = x - R;
        output_intersections_before(left);
        remove_circles_before(left);
        mark_intersections_inside(c);
        insert_intersections(c);
        insert_circle(c);
    }

    void end() {
        output_intersections_before(std::numeric_limits<double>::infinity());
        remove_circles_before(std::numeric_limits<double>::infinity());
        DEBUG_END();
    }

    void output_intersections_before(double left) {
        if (std::isfinite(left))
            LOG("Output intersections before " << left);
        else
            LOG("Output remaining intersections");
        while (i_queue.size() > 0 && i_queue.top().x < left) {
            auto i = i_line.lower_bound(i_queue.top());
            if (i->i != std::numeric_limits<size_t>::max()) {
                output(*i);
            }
            i_line.erase(i);
            i_queue.pop();
        }
    }

    void remove_circles_before(double left) {
        if (std::isfinite(left))
            LOG("Remove circles before " << left);
        else
            LOG("Remove remaining circles");
        while (c_queue.size() > 0 && c_queue.top().x < left - R) {
            LOG("Remove " << c_queue.top());
            auto i = c_alone.find(c_queue.top());
            if (i != c_alone.end()) {
                LOG("Circle was all alone");
                output_alone(*i);
                c_alone.erase(i);
            }
            c_line.erase(c_queue.top());
            c_queue.pop();
        }
    }

    void mark_intersections_inside(circle c) {
        double y1 = c.y - R, y2 = c.y + R;
        intersection p1 { 0, 0, 0, y1 }, p2 { 0, 0, 0, y2 };
        auto i1 = i_line.lower_bound(p1);
        auto i2 = i_line.lower_bound(p2);
        bool alone = true;
        for (auto i = i1; i != i2; ++i) {
            if (d_sq(c, *i) < R_sq) {
                alone = false;
                const size_t & i_i = i->i;
                LOG("Mark intersection " << *i << " inside " << c);
                const_cast<size_t &>(i_i) = std::numeric_limits<size_t>::max();
                LOG("After mark: " << *i);
                DEBUG_CIRCLE(i->x, i->y, R/5, "red");
                DEBUG_LINE(i->x, i->y, c.x, c.y, 0.02, "yellow");
            }
        }
        if (alone) {
            LOG("Insert " << c << " in alone set");
            c_alone.insert(c);
        }
    }

    void insert_intersections(circle c) {
        double y1 = c.y - twoR, y2 = c.y + twoR;
        circle c1 { 0, 0, y1 }, c2 { 0, 0, y2 };
        auto i1 = c_line.lower_bound(c1);
        auto i2 = c_line.lower_bound(c2);
        std::vector<circle> candidates(i1, i2);
        LOG(candidates.size() << " candidate(s) for intersection with " << c);
        insert_intersections_help(c, std::move(candidates));
    }

    void insert_intersections_help(circle c, std::vector<circle> candidates) {
        for (size_t i = 0; i < candidates.size(); ++i) {
            if (d_sq(c, candidates[i]) < twoR_sq) {
                c_alone.erase(candidates[i]);
                insert_intersection_check(
                    compute_intersection(c, candidates[i]), candidates);
                insert_intersection_check(
                    compute_intersection(candidates[i], c), candidates);
            }
        }
    }

    static double d_sq(circle c1, circle c2) {
        double dx = c1.x - c2.x, dy = c1.y - c2.y;
        return dx * dx + dy * dy;
    }

    static double distance(circle c1, circle c2) {
        double dx = c2.x - c1.x, dy = c2.y - c1.y;
        return std::hypot(dx, dy);
    }

    static double d_sq(circle c1, intersection c2) {
        double dx = c2.x - c1.x, dy = c2.y - c1.y;
        return dx * dx + dy * dy;
    }

    intersection compute_intersection(circle c1, circle c2) {
        // Consider the vector v from c1 to c2,
        // and let M = c1 + v/2 be the midpoint between c1 and c2.
        // We wish to compute the intersection P between c1 and c2.
        // Since there are two intersection points, we let P be the intersection
        // point to the left of the vector from c1 to M.
        // The three points {c1, M, P} form a right triangle with hypothenuse R
        // and side length |v/2|.
        // http://stackoverflow.com/a/3349134/1570972
        // http://paulbourke.net/geometry/circlesphere/
        // v [vx, vy] is the vector from c1 to c2.
        const double vx = c2.x - c1.x;
        const double vy = c2.y - c1.y;
        const double d = distance(c1, c2);
        // a = |v/2| is the length of the triangle side adjacent to c1.
        //const double a = d / 2;
        const double a_sq = d_sq(c1, c2) / 4;  // a_sq == a * a
        // h is the length of the triangle side opposite c1.
        const double h_sq = R_sq - a_sq;
        const double h = std::sqrt(h_sq);
        // M = [c1.x + vx / 2, c1.y + vy / 2] is the corner of the triangle.
        // u = [-vy/d, vx/d] is a normal vector orthogonal to v.
        // The intersection point P is thus M + h u.
        return intersection {
            c1.i, c2.i,
            c1.x + vx / 2 - vy * (h / d),
            c1.y + vy / 2 + vx * (h / d),
        };
    }

    intersection compute_intersection_trig(circle c1, circle c2) {
        // Let phi be the positive acute angle between c1M and c1P.
        const double v = distance(c1, c2);
        const double c1M_angle = std::atan2(c2.y - c1.y, c2.x - c1.x);
        const double phi = std::acos((v/2) / R);
        const double c1P_angle = c1M_angle + phi;
        return intersection {
            c1.i, c2.i,
            c1.x + std::cos(c1P_angle) * R,
            c1.y + std::sin(c1P_angle) * R,
        };
    }

    void insert_intersection_check(intersection o, const std::vector<circle> & candidates) {
        // If o is not contained within any of the candidates,
        // insert it into i_line and i_queue
        for (size_t i = 0; i < candidates.size(); ++i) {
            if (candidates[i].i != o.i && candidates[i].i != o.j && d_sq(candidates[i], o) < R_sq) {
                LOG("Intersection " << o << " intersects " << candidates[i]);
                DEBUG_CIRCLE(o.x, o.y, R/5, "red");
                DEBUG_LINE(o.x, o.y, candidates[i].x, candidates[i].y, 0.02, "green");
                return;
            }
        }
        LOG("Intersection " << o << " intersects no existing circle");
        i_line.insert(o);
        i_queue.push(o);
    }

    void insert_circle(circle c) {
        LOG("Insert circle " << c);
        DEBUG_CIRCLE(c.x, c.y, R, "black");
        c_line.insert(c);
        c_queue.push(c);
    }

    void output(intersection i) {
        std::cout << i.i << ' ' << i.j << ' ' << i.x << ' ' << i.y << std::endl;
        DEBUG_CIRCLE(i.x, i.y, R/5, "blue");
    }

    void output_alone(circle c) {
        std::cout << c.i << ' ' << c.i << ' ' << c.x << ' ' << c.y << std::endl;
        DEBUG_CIRCLE(c.x, c.y, R, "purple");
    }

private:
    size_t n_circle;
    std::set<circle, circle_by_y> c_alone;
    std::set<circle, circle_by_y> c_line;
    std::priority_queue<circle, std::vector<circle>, circle_by_greater_x> c_queue;
    std::set<intersection, intersection_by_y> i_line;
    std::priority_queue<intersection, std::vector<intersection>, intersection_by_greater_x> i_queue;
};

int main() {
    boundary b;
    double x, y;
    b.begin();
    while (std::cin >> x >> y) b.push(x, y);
    b.end();
    return 0;
}
