import numpy as np
import random as rn
from enum import IntEnum
import unit_test as ut


class HardLocationCreation(IntEnum):
    Nothing   = 0
    Random    = 1
    Uniform   = 2
    OnDemand  = 3


class Address(object):
    """
    To be used as an address in an SDM
    """
    address_length = 10

    @staticmethod
    def create_random(length):
        return ''

    @staticmethod
    def create_address_from_number(i):
        return Address('0')

    @staticmethod
    def get_null_value(length):
        return ''

    @staticmethod
    def get_value_to_increment_counter(value):
        return value

    @staticmethod
    def get_value_from_counters(counters):
        return counters

    def __init__(self, value):
        self.value     = value
        self.current_i = 0

    def __iter__(self):
        self.current_i = 0
        return self

    def __next__(self):
        if self.current_i >= len(self.value):
            raise StopIteration
        value = self.value[self.current_i]
        self.current_i += 1
        return value

    def distance(self, other_address):
        return 0

    def get_random_near_address(self, near_distance):
        """
        Returns a random address close to the original one (no longer than near_distance)
        :param near_distance:
        :return:
        """
        pass

    def __str__(self):
        return self.value


class BinaryAddress(Address):
    @staticmethod
    def create_address_from_number(i):
        return BinaryAddress(np.binary_repr(i, width=Address.address_length))

    @staticmethod
    def get_null_value(length):
        return '0' * length

    @staticmethod
    def get_value_to_increment_counter(value):
        return 1 if value == '1' else 0

    @staticmethod
    def get_value_from_counters(counters):
        return ''.join(['1' if counter > 0.0 else '0' for counter in counters])

    def __init__(self, value):
        super().__init__(value)

    def distance(self, other_address):
        return hamming_distance(self.value, other_address.value)

    def get_random_near_address(self, near_distance):
        """
        Returns a random address close to the original one (no longer than near_distance)
        :param near_distance:
        :return:
        """
        new_address = ''
        to_change = [rn.randint(0, Address.address_length - 1) for _ in range(near_distance)]
        for i, bit in enumerate(self.value):
            if i in to_change:
                bit1 = '1' if bit == '0' else '0'
            else:
                bit1 = bit
            new_address += bit1
        return BinaryAddress(new_address)


class IntegersAddress(Address):
    min_value = 0
    max_value = 255

    @staticmethod
    def create_random(length):
        return IntegersAddress([rn.randint(IntegersAddress.min_value, IntegersAddress.max_value)
                                for _ in range(length)])

    @staticmethod
    def get_null_value(length):
        return [0 for _ in range(length)]

    @staticmethod
    def get_value_to_increment_counter(value):
        return value

    @staticmethod
    def get_value_from_counters(counters):
        return [IntegersAddress.get_value_in_range(value) for value in counters]

    @staticmethod
    def get_value_in_range(value):
        return get_int_in_range(value, IntegersAddress.min_value, IntegersAddress.max_value)

    def __init__(self, value):
        super().__init__(value)

    def distance(self, other_address):
        distance = 0
        for i, value in enumerate(self.value):
            distance += abs(value - other_address.value[i])
        return distance

    def get_random_near_address(self, near_distance):
        """
        Returns a random address close to the original one (no farther than near_distance)
        :param near_distance:
        :return:
        """
        new_address = []
        k           = rn.randint(4, near_distance-1)  # number of elements to change
        k           = min(len(self.value), k)
        segments    = get_random_partition(near_distance, k)                   # value to change in each element
        to_change   = [rn.randint(0, len(self.value) - 1) for _ in range(k)]  # item to change
        for i, value in enumerate(self.value):
            if i in to_change:
                sign   = -1 if rn.random() < 0.5 else 1
                value1 = self.get_value_in_range(value + sign * segments[i])
            else:
                value1 = value
            new_address.append(value1)
        return IntegersAddress(new_address)

    def __str__(self):
        return ','.join([str(i) for i in self.value])


class SDM(object):
    """
    Main class with the basic functionalities for any kind of SDM
    see: https://en.wikipedia.org/wiki/Sparse_distributed_memory
    """

    def __init__(self, address_length, content_length, number_of_hard_locations, radius, values_per_dimension=2,
                 hard_location_creation=HardLocationCreation.Random, min_near_hard_locations=3,
                 address_class=Address, content_class=Address, debug=False):
        self.address_length           = address_length
        self.content_length           = content_length
        self.values_per_dimensions    = values_per_dimension
        self.max_possible_values      = self.values_per_dimensions ** self.content_length
        self.number_of_hard_locations = number_of_hard_locations
        self.min_near_hard_locations  = min_near_hard_locations
        self.radius                   = radius
        self.hard_locations_creation  = hard_location_creation

        self.address_class                = address_class
        self.address_class.address_length = self.address_length
        self.content_class                = content_class
        self.content_class.address_length = self.content_length

        self.hard_locations = self.initialize_hard_location(debug=debug)

    def write(self, address, content):
        near_hard_locations = self.get_hard_locations_in_distance(address, self.radius)
        if self.hard_locations_creation == HardLocationCreation.OnDemand and \
                len(near_hard_locations) < self.min_near_hard_locations:
            self.create_hard_locations_on_demand(address, content, near_hard_locations, near_distance=self.radius)
        else:
            for hard_location in near_hard_locations:
                self.update_hard_location_counters(hard_location, content)

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
            content = self.content_class.get_value_from_counters(avg)
        else:
            # no content associated with this address, return null value
            # print(self.content_class.address_length)
            content = self.content_class.get_null_value(self.content_length)
        return content

    def initialize_hard_location(self, debug=False):
        if self.hard_locations_creation == HardLocationCreation.Nothing:
            hard_locations = []
        elif self.hard_locations_creation == HardLocationCreation.Random:
            hard_locations = self.create_random_hard_locations(debug=debug)
        elif self.hard_locations_creation == HardLocationCreation.Uniform:
            hard_locations = create_uniform_hard_locations(self.number_of_hard_locations, self.max_possible_values,
                                                           self.address_length, self.content_length, debug=debug)
        elif self.hard_locations_creation == HardLocationCreation.OnDemand:
            # do nothing on creation time
            hard_locations = []
        else:
            raise Exception('%s for hard locations initialization is not implemented yet' %
                            self.hard_locations_creation)
        return hard_locations

    def create_random_hard_locations(self, debug=False):
        if debug:
            print('create %s random locations' % self.number_of_hard_locations)
        hard_locations = []
        for i in range(self.number_of_hard_locations):
            address = self.create_random_address()
            hard_locations.append(create_hard_location(address, self.content_length))
            if debug:
                print('   i:%s address:%s' % (i, address))
        return hard_locations

    def create_random_address(self):
        j = rn.randint(0, self.max_possible_values)
        return self.address_class.create_address_from_number(j)

    def create_hard_locations_on_demand(self, address, content, near_hard_locations, near_distance=3):
        """
        Applies the Dynamic Allocation algorithm as defined in
           https://link.springer.com/content/pdf/10.1007/978-3-540-30115-8_33.pdf
        :param near_distance:
        :param address: :type Address
        :param content:
        :param near_hard_locations:
        :return:
        """
        address_obj        = self.address_class(address)
        new_hard_locations = [address_obj] if len(near_hard_locations) == 0 else near_hard_locations
        new_n              = len(new_hard_locations)
        if new_n < self.min_near_hard_locations:
            # complement with randomly near locations
            for _ in range(self.min_near_hard_locations - new_n):
                new_hard_locations.append(address_obj.get_random_near_address(near_distance))

        # delete hard locations if maximum in reached
        tries = 0
        while len(self.hard_locations) >= self.number_of_hard_locations:
            to_delete_i = rn.randint(0, len(self.number_of_hard_locations)-1)
            to_delete_hard_location = self.hard_locations[to_delete_i]
            if to_delete_hard_location[0] in new_hard_locations:
                # do not delete the active ones
                tries += 1
                if tries > 1000:
                    raise Exception('too much tries deleting hard locations')
                continue
            del self.hard_locations[to_delete_i]

        # store content in each of the new addresses
        for new_address in new_hard_locations:
            hard_location = create_hard_location(new_address, self.content_length)
            self.update_hard_location_counters(hard_location, content)
            self.hard_locations.append(hard_location)

    def update_hard_location_counters(self, hard_location, content):
        for i, value in enumerate(content):
            hard_location[1][i] += self.content_class.get_value_to_increment_counter(value)

    def get_hard_locations_in_distance(self, address, distance):
        """
        Returns the list of hard location that are near address
        :param address:
        :param distance: distance to be considered near
        :return:
        """
        address_obj      = self.address_class(address)
        hard_in_distance = [hard_location for hard_location in self.hard_locations
                            if address_obj.distance(hard_location[0]) <= distance]
        return hard_in_distance

    def print_hard_locations(self, title='Hard Locations'):
        print(title)
        for hard_location in self.hard_locations:
            print('   %s -> %s' % (hard_location[0], hard_location[1]))


class BinarySDM(SDM):
    """
    Address and Content is binary
    """

    def __init__(self, address_length, content_length, number_of_hard_locations, radius,
                 hard_location_creation=HardLocationCreation.Nothing, debug=False):
        super().__init__(address_length, content_length, number_of_hard_locations, radius, values_per_dimension=2,
                         hard_location_creation=hard_location_creation, address_class=BinaryAddress,
                         content_class=BinaryAddress, debug=debug)


class ArithmeticSDM(SDM):
    """
    Address and Content are list of Integers as defined in
       https://www.iaeng.org/IJCS/issues_v39/issue_4/IJCS_39_4_03.pdf
    """

    def __init__(self, address_length, content_length, number_of_hard_locations, radius, learning_rate=1.0,
                 values_per_dimension=255, hard_location_creation=HardLocationCreation.Nothing, debug=False):
        self.learning_rate = learning_rate
        super().__init__(address_length, content_length, number_of_hard_locations, radius,
                         values_per_dimension=values_per_dimension, hard_location_creation=hard_location_creation,
                         address_class=IntegersAddress, content_class=IntegersAddress, debug=debug)

    def create_random_address(self):
        return self.address_class.create_random(self.address_length)

    def update_hard_location_counters(self, hard_location, content):
        for i, value in enumerate(content):
            hard_location[1][i] += self.learning_rate * \
                                   (self.content_class.get_value_to_increment_counter(value) - hard_location[1][i])


# Hard location functions
def create_hard_location(address, content_length, counter_type=int):
    return address, np.zeros(content_length, dtype=counter_type)


def create_random_hard_locations(number_of_hard_locations, max_possible_values, address_class, content_length,
                                 debug=False):
    if debug:
        print('create %s random locations' % number_of_hard_locations)
    hard_locations = []
    for i in range(number_of_hard_locations):
        j       = rn.randint(0, max_possible_values)
        address = address_class.create_address_from_number(j)
        hard_locations.append(create_hard_location(address, content_length))
        if debug:
            print('   i:%s j:%s address:%s' % (i, j, address))
    return hard_locations


def create_uniform_hard_locations(number_of_hard_locations, max_possible_values, address_class, content_length,
                                  debug=False):
    distance = int(max_possible_values / number_of_hard_locations)
    if debug:
        print('create %s hard locations (d:%s)' % (number_of_hard_locations, distance))
    j = distance
    hard_locations = []
    for _ in range(number_of_hard_locations):
        address = address_class.create_address_from_number(j)
        hard_locations.append(create_hard_location(address, content_length))
        if debug:
            print('   j:%s address:%s' % (j, address))
        j += distance
    return hard_locations


# other functions
def get_random_partition(n, k):
    """
    Returns a list of k elements whose total value is n
    :param n:
    :param k:
    :return:
    """
    # Ensure that k is not greater than n to avoid segments with a value of 0
    if k > n:
        raise ValueError("k should not be greater than n to avoid segments with a value of 0.")

    # Generate k-1 unique cut points within the range of 1 to n-1
    cuts = sorted(rn.sample(range(1, n), k - 1))

    # Initialize the list of segments
    segments = []

    # The start of the first segment is 0
    start = 0

    # For each cut point, calculate the segment and update the start for the next one
    for cut in cuts:
        segments.append(cut - start)
        start = cut

    # Add the last segment from the last cut to n
    segments.append(n - start)

    return segments


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


def get_int_in_range(value, min_value, max_value):
    i = int(value)
    i = max(min_value, min(max_value, i))
    return i


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
    address_class = BinaryAddress
    address_class.address_length = address_length
    hard_locations = create_random_hard_locations(number_of_hard_locations, max_possible_values, address_class,
                                                  content_length, debug=debug)
    return len(hard_locations)


def test_arithmetic_distance(address1, address2):
    a1 = IntegersAddress(address1)
    a2 = IntegersAddress(address2)
    return a1.distance(a2)


def test_random_near_address(address, distance):
    address_obj = BinaryAddress(address)
    near_address = address_obj.get_random_near_address(distance)
    return near_address


def test_create_uniform_hard_locations(number_of_hard_locations, max_possible_values, address_length, content_length,
                                       debug):
    address_class = BinaryAddress
    address_class.address_length = address_length
    hard_locations = create_uniform_hard_locations(number_of_hard_locations, max_possible_values, address_class,
                                                   content_length, debug=debug)
    return len(hard_locations)


def test_binary_sdm_write_read(address_length, content_length, number_of_hard_locations, radius, debug, hard_locations,
                               writes, reads):
    hard_location_creation = HardLocationCreation.OnDemand if len(hard_locations) == 0 else HardLocationCreation.Nothing
    sdm = BinarySDM(address_length, content_length, number_of_hard_locations, radius,
                    hard_location_creation=hard_location_creation, debug=debug)
    sdm.hard_locations = [create_hard_location(sdm.address_class(address), content_length)
                          for address in hard_locations]
    for [address, content] in writes:
        sdm.write(address, content)
    if debug:
        sdm.print_hard_locations(title='Hard locations after write')
    values = [sdm.read(read) for read in reads]
    return values


def test_arithmetic_sdm_write_read(address_length, content_length, number_of_hard_locations, radius, debug,
                                   hard_locations, writes, reads):
    hard_location_creation = HardLocationCreation.OnDemand if len(hard_locations) == 0 else HardLocationCreation.Nothing
    sdm = ArithmeticSDM(address_length, content_length, number_of_hard_locations, radius,
                        hard_location_creation=hard_location_creation, debug=debug)
    sdm.hard_locations = [create_hard_location(sdm.address_class(address), content_length)
                          for address in hard_locations]
    for [address, content] in writes:
        sdm.write(address, content)
    if debug:
        sdm.print_hard_locations(title='Hard locations after write')
    values = [sdm.read(read) for read in reads]
    return values


def test_get_random_partition(n, k, debug):
    segments = get_random_partition(n, k)
    if debug:
        print('segments for %s/%s: %s' % (n, k, segments))
    return len(segments)


if __name__ == "__main__":
    ut.UnitTest(__name__, 'tests/SDM.test', '')
