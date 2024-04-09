import numpy as np
import random as rn
from enum import IntEnum
import unit_test as ut


class HardLocationCreation(IntEnum):
    Nothing   = 0
    Random    = 1
    Uniform   = 2
    OnDemand  = 3


class SDM(object):
    """
    Main class with the basic functionalities for any kind of SDM
    see: https://en.wikipedia.org/wiki/Sparse_distributed_memory
    """

    def __init__(self, address_length, content_length, number_of_hard_locations, radius, values_per_dimension=2,
                 hard_location_creation=HardLocationCreation.Random, min_near_hard_locations=3, debug=False):
        self.address_length           = address_length
        self.content_length           = content_length
        self.values_per_dimensions    = values_per_dimension
        self.max_possible_values      = self.values_per_dimensions ** self.content_length
        self.number_of_hard_locations = number_of_hard_locations
        self.min_near_hard_locations  = min_near_hard_locations
        self.radius                   = radius
        self.hard_locations_creation  = hard_location_creation

        self.hard_locations = self.initialize_hard_location(debug=debug)

    def write(self, address, content):
        near_hard_locations = self.get_hard_locations_in_distance(address, self.radius)
        if self.hard_locations_creation == HardLocationCreation.OnDemand and \
                len(near_hard_locations) < self.min_near_hard_locations:
            self.create_hard_locations_on_demand(address, content, near_hard_locations)
        else:
            for hard_location in near_hard_locations:
                for i, bit in enumerate(content):
                    inc = 1 if bit == '1' else -1
                    hard_location[1][i] += inc

    def read(self, address):
        # print('read %s' % address)
        counter = np.zeros(self.content_length, dtype=float)
        total   = 0
        for hard_location in self.get_hard_locations_in_distance(address, self.radius):
            # print('      near hard location %s -> %s' % (hard_location[0], hard_location[1]))
            total += 1
            for i, value in enumerate(hard_location[1]):
                counter[i] += value
        if total > 0:
            avg     = counter/total
            content = ''.join(['1' if v >= 0.0 else '0' for v in avg])
        else:
            # no content associated with this address, return null value
            content = self.get_null_content()
        return content

    def get_null_content(self):
        return '0' * self.content_length

    def initialize_hard_location(self, debug=False):
        if self.hard_locations_creation == HardLocationCreation.Nothing:
            hard_locations = []
        elif self.hard_locations_creation == HardLocationCreation.Random:
            hard_locations = create_random_hard_locations(self.number_of_hard_locations, self.max_possible_values,
                                                          self.address_length, self.content_length, debug=debug)
        elif self.hard_locations_creation == HardLocationCreation.Uniform:
            hard_locations = create_uniform_hard_locations(self.number_of_hard_locations, self.max_possible_values,
                                                           self.address_length, self.content_length, debug=debug)
        elif self.hard_locations_creation == HardLocationCreation.OnDemand:
            # do nothing on creation time
            hard_locations = []
        else:
            raise Exception('%s for hard locations initialization is not implemented yet' % self.hard_locations_creation)
        return hard_locations

    def create_hard_locations_on_demand(self, address, content, near_hard_locations, near_distance=3):
        """
        Applies the Dynamic Allocation algorithm as defined in
           https://link.springer.com/content/pdf/10.1007/978-3-540-30115-8_33.pdf
        :param near_distance:
        :param address:
        :param content:
        :param near_hard_locations:
        :return:
        """
        new_hard_locations = [address] if len(near_hard_locations) == 0 else near_hard_locations
        new_n = len(new_hard_locations)
        if new_n < self.min_near_hard_locations:
            # complement with randomly near locations
            for _ in range(self.min_near_hard_locations - new_n):
                new_hard_locations.append(random_near_address(address, near_distance))
        for new_address in new_hard_locations:
            hard_location = create_hard_location(new_address, self.content_length)
            for i, bit in enumerate(content):
                hard_location[1][i] += 1 if bit == '1' else -1
            self.hard_locations.append(hard_location)

    def get_hard_locations_in_distance(self, address, distance):
        """
        Returns the list of hard location that are near address
        :param address:
        :param distance: distance to be considered near
        :return:
        """
        hard_in_distance = [hard_location for hard_location in self.hard_locations
                            if self.address_distance(address, hard_location[0]) <= distance]
        return hard_in_distance

    def address_distance(self, address1, address2):
        # print('   distance from %s to %s is %s' % (address1, address2, hamming_distance(address1, address2)))
        return hamming_distance(address1, address2)

    def print_hard_locations(self, title='Hard Locations'):
        print(title)
        for hard_location in self.hard_locations:
            print('   %s -> %s' % (hard_location[0], hard_location[1]))


class BinarySDM(SDM):
    """
    Content is a binary message
    """

    def address_distance(self, address1, address2):
        return hamming_distance(address1, address2)

    def __init__(self, address_length, content_length, number_of_hard_locations, radius,
                 hard_location_creation=HardLocationCreation.Nothing):
        super().__init__(address_length, content_length, number_of_hard_locations, radius, values_per_dimension=2,
                         hard_location_creation=hard_location_creation)


# Hard location creation
def create_hard_location(address, content_length, counter_type=int):
    return address, np.zeros(content_length, dtype=counter_type)


def create_binary_address(i, address_length):
    return np.binary_repr(i, width=address_length)


def create_random_hard_locations(number_of_hard_locations, max_possible_values, address_length,
                                 content_length, debug=False):
    if debug:
        print('create %s random locations' % number_of_hard_locations)
    hard_locations = []
    for i in range(number_of_hard_locations):
        j       = rn.randint(0, max_possible_values)
        address = create_binary_address(j, address_length)
        hard_locations.append(create_hard_location(address, content_length))
        if debug:
            print('   i:%s j:%s address:%s' % (i, j, address))
    return hard_locations


def create_uniform_hard_locations(number_of_hard_locations, max_possible_values, address_length,
                                  content_length, debug=False):
    distance = int(max_possible_values / number_of_hard_locations)
    if debug:
        print('create %s hard locations (d:%s)' % (number_of_hard_locations, distance))
    j = distance
    hard_locations = []
    for _ in range(number_of_hard_locations):
        address = create_binary_address(j, address_length)
        hard_locations.append(create_hard_location(address, content_length))
        if debug:
            print('   j:%s address:%s' % (j, address))
        j += distance
    return hard_locations


def random_near_address(address, near_distance):
    """
    Returns a random address close to the original one (no longer than near_distance)
    :param address:
    :param near_distance:
    :return:
    """
    new_address = ''
    to_change   = [rn.randint(0, len(address)-1) for _ in range(near_distance)]
    for i, bit in enumerate(address):
        if i in to_change:
            bit1 = '1' if bit == '0' else '0'
        else:
            bit1 = bit
        new_address += bit1
    return new_address


# other functions
def hamming_distance(binary1, binary2):
    """
    Returns the Hamming distance between to binary numbers
    :param binary1:
    :param binary2:
    :return:
    """
    d = 0
    for i in range(len(binary1)):
        if binary1[i] == binary2[i]:
            continue
        d += 1
    return d


# Tests
def test_create_hard_locations(address_length, content_length, number_of_hard_locations, radius, values_per_dimension,
                               debug):
    sdm = SDM(address_length, content_length, number_of_hard_locations, radius,
              values_per_dimension=values_per_dimension, debug=debug)
    return len(sdm.hard_locations)


def test_near_hard_locations(address, radius, hard_locations):
    near = [hard_location for hard_location in hard_locations if hamming_distance(address, hard_location) <= radius]
    return near


def test_create_random_hard_locations(number_of_hard_locations, max_possible_values, address_length, content_length,
                                      debug):
    hard_locations = create_random_hard_locations(number_of_hard_locations, max_possible_values, address_length,
                                                  content_length, debug=debug)
    return len(hard_locations)


def test_create_uniform_hard_locations(number_of_hard_locations, max_possible_values, address_length, content_length,
                                       debug):
    hard_locations = create_uniform_hard_locations(number_of_hard_locations, max_possible_values, address_length,
                                                   content_length, debug=debug)
    return len(hard_locations)


def test_sdm_write_read(address_length, content_length, number_of_hard_locations, radius, values_per_dimension, debug,
                        hard_locations, writes, reads):
    hard_location_creation = HardLocationCreation.OnDemand if len(hard_locations) == 0 else HardLocationCreation.Nothing
    sdm = SDM(address_length, content_length, number_of_hard_locations, radius,
              values_per_dimension=values_per_dimension, hard_location_creation=hard_location_creation,
              debug=debug)
    sdm.hard_locations = [create_hard_location(address, content_length) for address in hard_locations]
    for [address, content] in writes:
        sdm.write(address, content)
    if debug:
        sdm.print_hard_locations(title='Hard locations after write')
    values = [sdm.read(read) for read in reads]
    return values


if __name__ == "__main__":
    ut.UnitTest(__name__, 'tests/SDM.test', '')
