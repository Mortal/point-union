CXX := c++
CXXFLAGS := -std=c++14 -Wall -Wextra -O3

all: union

union: union.o
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

union.o: %.o: %.cpp
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -c -o $@ $<
